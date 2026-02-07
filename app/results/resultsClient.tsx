"use client";

import { useSearchParams } from "next/navigation";
import data from "../../data/tn_cutoffs.json";
import { predictColleges } from "../../utils/predictorLogic";
import CollegeCard from "../components/CollegeCard";

export default function ResultsClient() {
  const searchParams = useSearchParams();

  const marks = Number(searchParams.get("marks"));
  const category = searchParams.get("category") || "OC";
  const quota = searchParams.get("quota") || "State";

  const results = predictColleges(marks, category, quota, data);

  return (
    <div className="min-h-screen p-6 bg-gray-100">
      <h1 className="text-3xl font-bold mb-4">
        Prediction Results
      </h1>

      <p className="mb-6">
        Marks: <b>{marks}</b> | Category: <b>{category}</b> | Quota:{" "}
        <b>{quota}</b>
      </p>

      <div className="grid gap-4">
        {results.length > 0 ? (
          results.map((c, i) => (
            <CollegeCard key={i} college={c} />
          ))
        ) : (
          <p className="text-red-600">
            No colleges found for this score range.
          </p>
        )}
      </div>
    </div>
  );
}
