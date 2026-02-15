"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import data from "../../data/tn_cutoffs.json";

type CutoffSummary = {
  course: string;
  community: string;
  quota: string;
  category: string;
  college_type: string;
};

const FORM_STORAGE_KEY = "neet_predictor_form_v1";

type StoredFormState = {
  marks?: string;
  course?: string;
  community?: string;
  category?: string;
  quota?: string;
  collegeType?: string;
};

function getCategoriesForQuota(quota: string): string[] {
  const values = (data as CutoffSummary[])
    .filter((item) => item.quota?.trim() === quota)
    .map((item) => item.category?.trim())
    .filter((value): value is string => Boolean(value));

  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
}

function getPreferredCategoryForQuota(quota: string, categories: string[]): string {
  const preferredByQuota: Record<string, string> = {
    GOVT: "Government Quota",
    "7.5%": "Government Quota",
    EXSRVC: "Government Quota",
    PWD: "Government Quota",
    SPORTS: "Government Quota",
    MGMT: "Management Quota",
  };

  const preferred = preferredByQuota[quota];
  if (preferred && categories.includes(preferred)) {
    return preferred;
  }

  return categories[0] ?? "";
}

function getInitialFormState(): Required<StoredFormState> {
  const defaults: Required<StoredFormState> = {
    marks: "",
    course: "",
    community: "OC",
    category: "Government Quota",
    quota: "GOVT",
    collegeType: "",
  };

  if (typeof window === "undefined") {
    return defaults;
  }

  const saved = window.localStorage.getItem(FORM_STORAGE_KEY);
  if (!saved) {
    return defaults;
  }

  try {
    const parsed = JSON.parse(saved) as StoredFormState;
    const quota = parsed.quota ?? defaults.quota;
    const allowedCategories = getCategoriesForQuota(quota);
    const category = parsed.category ?? defaults.category;
    const preferredCategory = getPreferredCategoryForQuota(quota, allowedCategories);

    return {
      marks: parsed.marks ?? defaults.marks,
      course: parsed.course ?? defaults.course,
      community: parsed.community ?? defaults.community,
      category: allowedCategories.includes(category)
        ? category
        : (preferredCategory || defaults.category),
      quota,
      collegeType: parsed.collegeType ?? defaults.collegeType,
    };
  } catch {
    return defaults;
  }
}

export default function PredictorForm() {
  const router = useRouter();
  const initialState = getInitialFormState();

  const [marks, setMarks] = useState(initialState.marks);
  const [course, setCourse] = useState(initialState.course);
  const [community, setCommunity] = useState(initialState.community);
  const [category, setCategory] = useState(initialState.category);
  const [quota, setQuota] = useState(initialState.quota);
  const [collegeType, setCollegeType] = useState(initialState.collegeType);

  const courses = useMemo(() => {
    const values = (data as CutoffSummary[])
      .map((item) => item.course?.trim())
      .filter((value): value is string => Boolean(value));

    return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
  }, []);

  const communities = useMemo(() => {
    const values = (data as CutoffSummary[])
      .map((item) => item.community?.trim())
      .filter((value): value is string => Boolean(value));

    return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
  }, []);

  const categories = useMemo(() => {
    return getCategoriesForQuota(quota);
  }, [quota]);

  const collegeTypes = useMemo(() => {
    const values = (data as CutoffSummary[])
      .map((item) => item.college_type?.trim())
      .filter((value): value is string => Boolean(value));

    return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      FORM_STORAGE_KEY,
      JSON.stringify({
        marks,
        course,
        community,
        category,
        quota,
        collegeType,
      })
    );
  }, [marks, course, community, category, quota, collegeType]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams({
      marks,
      course,
      community,
      category,
      quota,
      collegeType,
    });

    router.push(`/results?${params.toString()}`);
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

      {/* Course */}
      <select
        value={course}
        onChange={(e) => setCourse(e.target.value)}
        className="w-full border p-2 rounded"
      >
        <option value="">Any Course</option>
        {courses.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      {/* Community */}
      <select
        value={community}
        onChange={(e) => setCommunity(e.target.value)}
        className="w-full border p-2 rounded"
      >
        {communities.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      {/* Quota */}
      <select
        value={quota}
        onChange={(e) => {
          const nextQuota = e.target.value;
          const nextCategories = getCategoriesForQuota(nextQuota);
          setQuota(nextQuota);
          setCategory(getPreferredCategoryForQuota(nextQuota, nextCategories));
        }}
        className="w-full border p-2 rounded"
      >
        <option>GOVT</option>
        <option>MGMT</option>
        <option>7.5%</option>
        <option>EXSRVC</option>
        <option>PWD</option>
        <option>SPORTS</option>
      </select>

      {/* Category */}
      <select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        className="w-full border p-2 rounded"
      >
        {categories.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      {/* College Type */}
      <select
        value={collegeType}
        onChange={(e) => setCollegeType(e.target.value)}
        className="w-full border p-2 rounded"
      >
        <option value="">Any College Type</option>
        {collegeTypes.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      <button className="w-full bg-blue-600 text-white py-2 rounded-lg">
        Predict Colleges
      </button>
    </form>
  );
}
