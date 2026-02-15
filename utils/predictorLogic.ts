export type CollegeSummary = {
  college: string;
  course: string;
  quota: string;
  category: string;
  community: string;
  college_type: string;
  round: string;
  year: number;
  rank_mean: number;
  rank_std: number;
  rank_min: number;
  rank_max: number;
  marks_mean: number;
  marks_std: number;
  marks_min: number;
  marks_max: number;
};

export type PredictedCollege = CollegeSummary & {
  probability: number;
  chance: "Low" | "Medium" | "High";
  allotmentRound: string;
  probabilityDetails: {
    method: "normal_cdf" | "min_max_linear" | "fallback";
    inputMarks: number;
    mean: number;
    std: number;
    min: number;
    max: number;
    zScore: number | null;
    rawScore: number;
  };
};

type PredictorFilters = {
  course: string;
  community: string;
  category: string;
  quota: string;
  collegeType: string;
};

type ConsolidatedCollege = CollegeSummary & {
  roundSummaries: CollegeSummary[];
};

function aggregateMeanStd(points: Array<{ mean: number; std: number }>) {
  if (points.length === 0) {
    return { mean: 0, std: 0 };
  }

  const valid = points.filter(
    (p) => Number.isFinite(p.mean) && Number.isFinite(p.std) && p.std >= 0
  );

  if (valid.length === 0) {
    return { mean: 0, std: 0 };
  }

  const mean = valid.reduce((sum, p) => sum + p.mean, 0) / valid.length;
  const secondMoment =
    valid.reduce((sum, p) => sum + (p.std * p.std + p.mean * p.mean), 0) / valid.length;
  const variance = Math.max(0, secondMoment - mean * mean);

  return { mean, std: Math.sqrt(variance) };
}

function consolidateAcrossRounds(data: CollegeSummary[]): ConsolidatedCollege[] {
  const grouped = new Map<string, CollegeSummary[]>();

  for (const item of data) {
    const key = [
      item.college,
      item.course,
      item.quota,
      item.category,
      item.community,
      item.college_type,
      String(item.year),
    ]
      .map((v) => v.trim().toLowerCase())
      .join("|");

    const list = grouped.get(key);
    if (list) {
      list.push(item);
    } else {
      grouped.set(key, [item]);
    }
  }

  return Array.from(grouped.values()).map((items) => {
    const base = items[0];

    const rankAgg = aggregateMeanStd(
      items.map((item) => ({ mean: item.rank_mean, std: item.rank_std }))
    );
    const marksAgg = aggregateMeanStd(
      items.map((item) => ({ mean: item.marks_mean, std: item.marks_std }))
    );

    return {
      ...base,
      round: "All Rounds",
      roundSummaries: items,
      rank_mean: rankAgg.mean,
      rank_std: rankAgg.std,
      rank_min: Math.min(...items.map((item) => item.rank_min)),
      rank_max: Math.max(...items.map((item) => item.rank_max)),
      marks_mean: marksAgg.mean,
      marks_std: marksAgg.std,
      marks_min: Math.min(...items.map((item) => item.marks_min)),
      marks_max: Math.max(...items.map((item) => item.marks_max)),
    };
  });
}

function roundOrder(round: string) {
  const match = round.match(/\d+/);
  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }
  return Number(match[0]);
}

function estimateAllotmentRound(rounds: CollegeSummary[], marks: number) {
  const rankedRounds = [...rounds]
    .map((item) => ({
      round: item.round,
      probability: probabilityFromStats(marks, item).rawScore,
    }))
    .sort((a, b) => roundOrder(a.round) - roundOrder(b.round));

  const strongRound = rankedRounds.find((item) => item.probability >= 0.5);
  if (strongRound) {
    return strongRound.round;
  }

  const possibleRound = rankedRounds.find((item) => item.probability > 0);
  if (possibleRound) {
    return possibleRound.round;
  }

  return "Not likely";
}

function matchOptionalFilter(value: string | undefined, selected: string) {
  const picked = selected.trim().toLowerCase();
  if (!picked) {
    return true;
  }
  if (!value) {
    return true;
  }
  return value.trim().toLowerCase() === picked;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

// Normal CDF approximation (Abramowitz-Stegun based erf approximation).
function normalCdf(z: number) {
  const sign = z < 0 ? -1 : 1;
  const x = Math.abs(z) / Math.sqrt(2);
  const t = 1 / (1 + 0.3275911 * x);
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const erf =
    1 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-x * x));
  return 0.5 * (1 + sign * erf);
}

function probabilityFromStats(
  marks: number,
  college: CollegeSummary
): PredictedCollege["probabilityDetails"] {
  const mean = college.marks_mean;
  const std = college.marks_std;
  const min = college.marks_min;
  const max = college.marks_max;

  if (!Number.isFinite(marks) || !Number.isFinite(mean)) {
    return {
      method: "fallback",
      inputMarks: marks,
      mean,
      std,
      min,
      max,
      zScore: null,
      rawScore: 0,
    };
  }

  if (Number.isFinite(min) && marks < min) {
    return {
      method: "fallback",
      inputMarks: marks,
      mean,
      std,
      min,
      max,
      zScore: null,
      rawScore: 0,
    };
  }

  if (Number.isFinite(std) && std > 0) {
    const zScore = (marks - mean) / std;
    return {
      method: "normal_cdf",
      inputMarks: marks,
      mean,
      std,
      min,
      max,
      zScore,
      rawScore: clamp(normalCdf(zScore), 0, 1),
    };
  }

  if (Number.isFinite(min) && Number.isFinite(max) && max > min) {
    return {
      method: "min_max_linear",
      inputMarks: marks,
      mean,
      std,
      min,
      max,
      zScore: null,
      rawScore: clamp((marks - min) / (max - min), 0, 1),
    };
  }

  return {
    method: "fallback",
    inputMarks: marks,
    mean,
    std,
    min,
    max,
    zScore: null,
    rawScore: marks >= mean ? 0.85 : 0.15,
  };
}

function chanceFromProbability(probability: number): "Low" | "Medium" | "High" {
  if (probability >= 0.75) {
    return "High";
  }
  if (probability >= 0.45) {
    return "Medium";
  }
  return "Low";
}

export function predictColleges(
  marks: number,
  filters: PredictorFilters,
  data: CollegeSummary[]
): PredictedCollege[] {
  const consolidated = consolidateAcrossRounds(data);

  const ranked = consolidated
    .filter(
      (c) =>
        matchOptionalFilter(c.course, filters.course) &&
        matchOptionalFilter(c.community, filters.community) &&
        matchOptionalFilter(c.category, filters.category) &&
        matchOptionalFilter(c.quota, filters.quota) &&
        matchOptionalFilter(c.college_type, filters.collegeType)
    )
    .map((c) => {
      const probabilityDetails = probabilityFromStats(marks, c);
      const probability = probabilityDetails.rawScore;
      const chance = chanceFromProbability(probability);
      const allotmentRound = estimateAllotmentRound(c.roundSummaries, marks);
      const { roundSummaries, ...college } = c;
      void roundSummaries;

      return { ...college, probability, chance, allotmentRound, probabilityDetails };
    })
    .filter((c) => c.probability >= 0.1);

  const bestByCollege = new Map<string, PredictedCollege>();

  for (const item of ranked) {
    const key = item.college.trim().toLowerCase();
    const current = bestByCollege.get(key);

    if (!current) {
      bestByCollege.set(key, item);
      continue;
    }

    const isBetter =
      item.probability > current.probability ||
      (item.probability === current.probability && item.marks_mean > current.marks_mean) ||
      (item.probability === current.probability &&
        item.marks_mean === current.marks_mean &&
        item.year > current.year);

    if (isBetter) {
      bestByCollege.set(key, item);
    }
  }

  return Array.from(bestByCollege.values()).sort(
    (a, b) => b.probability - a.probability || b.marks_mean - a.marks_mean
  );
}
