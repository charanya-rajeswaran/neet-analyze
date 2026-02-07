import { Suspense } from "react";
import ResultsClient from "./resultsClient.tsx";

export default function ResultsPage() {
  return (
    <Suspense fallback={<p className="p-6">Loading results...</p>}>
      <ResultsClient />
    </Suspense>
  );
}
