type Props = {
  college: {
    college: string;
    course: string;
    cutoff_marks: number;
    chance: string;
  };
};

export default function CollegeCard({ college }: Props) {
  return (
    <div className="p-4 bg-white shadow-md rounded-xl border">
      <h2 className="text-lg font-bold">{college.college}</h2>

      <p className="text-gray-600">Course: {college.course}</p>
      <p className="text-gray-600">Cutoff: {college.cutoff_marks}</p>

      <p className="mt-2 font-semibold">
        Chance:{" "}
        <span className="text-blue-600">{college.chance}</span>
      </p>
    </div>
  );
}
