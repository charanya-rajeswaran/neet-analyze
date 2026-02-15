import { PredictedCollege } from "../../utils/predictorLogic";

type Props = {
  college: PredictedCollege;
};

export default function CollegeCard({ college }: Props) {
  const probabilityPct = Math.round(college.probability * 100);
  const details = college.probabilityDetails;

  return (
    <div className="p-4 bg-white shadow-md rounded-xl border">
      <h2 className="text-lg font-bold">{college.college}</h2>

      <p className="text-gray-600">Course: {college.course}</p>
      <p className="text-gray-600">Community: {college.community}</p>
      <p className="text-gray-600">Category: {college.category}</p>
      <p className="text-gray-600">Quota: {college.quota}</p>
      <p className="text-gray-600">College Type: {college.college_type}</p>
      <p className="text-gray-600">Data Year: {college.year}</p>
      <p className="text-gray-600">Stats Scope: {college.round}</p>
      <p className="text-gray-700 font-medium">
        Expected Allotment Round: {college.allotmentRound}
      </p>

      <p className="mt-2 font-semibold">
        Chance:{" "}
        <span className="text-blue-600">{college.chance}</span> ({probabilityPct}%)
      </p>

      <details className="mt-3 text-sm text-gray-700">
        <summary className="cursor-pointer font-semibold">Debug: stats and calculation</summary>
        <div className="mt-2 space-y-1">
          <p>
            Marks Stats: mean {college.marks_mean}, std {college.marks_std}, min{" "}
            {college.marks_min}, max {college.marks_max}
          </p>
          <p>
            Rank Stats: mean {college.rank_mean}, std {college.rank_std}, min{" "}
            {college.rank_min}, max {college.rank_max}
          </p>
          {details.method === "normal_cdf" && (
            <p>
              Method: Normal CDF. z = (marks - mean) / std = ({details.inputMarks} -{" "}
              {details.mean}) / {details.std} = {details.zScore?.toFixed(3)}.
              Probability = Phi(z) = {probabilityPct}%.
            </p>
          )}
          {details.method === "min_max_linear" && (
            <p>
              Method: Min-Max Linear. score = (marks - min) / (max - min) = (
              {details.inputMarks} - {details.min}) / ({details.max} - {details.min}).
              Probability = {probabilityPct}%.
            </p>
          )}
          {details.method === "fallback" && (
            <p>
              Method: Fallback (insufficient spread or marks below minimum). Mean{" "}
              {details.mean}, min {details.min}. Probability = {probabilityPct}%.
            </p>
          )}
        </div>
      </details>
    </div>
  );
}
