"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function PredictorForm() {
  const router = useRouter();

  const [marks, setMarks] = useState("");
  const [category, setCategory] = useState("OC");
  const [quota, setQuota] = useState("State");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    router.push(
      `/results?marks=${marks}&category=${category}&quota=${quota}`
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="p-6 bg-white rounded-xl shadow-md space-y-4"
    >
      <h2 className="text-xl font-bold">
        Enter Your NEET Details
      </h2>

      {/* Marks */}
      <input
        type="number"
        value={marks}
        onChange={(e) => setMarks(e.target.value)}
        placeholder="Enter NEET Marks"
        className="w-full border p-2 rounded"
        required
      />

      {/* Category */}
      <select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        className="w-full border p-2 rounded"
      >
        <option>OC</option>
        <option>BC</option>
        <option>MBC</option>
        <option>SC</option>
        <option>ST</option>
      </select>

      {/* Quota */}
      <select
        value={quota}
        onChange={(e) => setQuota(e.target.value)}
        className="w-full border p-2 rounded"
      >
        <option>State</option>
        <option>AIQ</option>
      </select>

      <button className="w-full bg-blue-600 text-white py-2 rounded-lg">
        Predict Colleges
      </button>
    </form>
  );
}
