import PredictorForm from "../components/PredictorForm";

export default function PredictorPage() {
  return (
    <div className="min-h-screen flex justify-center items-center bg-gray-100 p-6">
      <div className="w-full max-w-xl">
        <p className="mb-3 text-sm text-gray-600">
          Note: Predictions are based on 2025 Tamil Nadu allotment results.
        </p>
        <PredictorForm />
      </div>
    </div>
  );
}
