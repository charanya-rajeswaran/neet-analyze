"use client";

import { useSearchParams } from "next/navigation";
import data from "../../data/tn_cutoffs.json";
import { predictColleges } from "../../utils/predictorLogic";
import CollegeCard from "../components/CollegeCard";

export default function ResultsClient() {
  const searchParams = useSearchParams();

  const marks = Number(searchParams.get("marks"));
  const course = searchParams.get("course") || "";
  const community = searchParams.get("community") || "";
  const category = searchParams.get("category") || "";
  const quota = searchParams.get("quota") || "State";
  const collegeType = searchParams.get("collegeType") || "";

  const results = predictColleges(
    marks,
    { course, community, category, quota, collegeType },
    data
  );

  return (
    <div className="min-h-screen p-6 bg-gray-100">
      <h1 className="text-3xl font-bold mb-4">
        Prediction Results
      </h1>
      <p className="mb-3 text-sm text-gray-600">
        Chance is estimated from historical marks distribution stats (mean/std/min/max).
      </p>
      <p className="mb-3 text-sm text-gray-600">
        Note: Results are based on 2025 Tamil Nadu allotment results.
      </p>

      <p className="mb-6">
        Marks: <b>{marks}</b> | Course: <b>{course || "Any"}</b> | Community: <b>{community || "Any"}</b> |
        {" "}Category: <b>{category || "Any"}</b> | Quota: <b>{quota || "Any"}</b> |
        {" "}College Type: <b>{collegeType || "Any"}</b>
      </p>

      <div className="grid gap-4">
        {results.length > 0 ? (
          results.map((c) => (
            <CollegeCard key={`${c.college}-${c.course}`} college={c} />
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
