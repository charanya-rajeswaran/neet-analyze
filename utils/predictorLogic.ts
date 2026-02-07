type College = {
  college: string;
  course: string;
  quota: string;
  category: string;
  cutoff_marks: number;
  chance?: string;
};

export function predictColleges(
  marks: number,
  category: string,
  quota: string,
  data: College[]
) {
  return data
    .filter(
      (c) =>
        c.category === category &&
        c.quota === quota &&
        marks >= c.cutoff_marks - 10
    )
    .map((c) => {
      let chance = "Low";

      if (marks >= c.cutoff_marks + 20) {
        chance = "High";
      } else if (marks >= c.cutoff_marks) {
        chance = "Medium";
      }

      return { ...c, chance };
    })
    .sort((a, b) => b.cutoff_marks - a.cutoff_marks);
}
