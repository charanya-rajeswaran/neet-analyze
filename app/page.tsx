import Link from "next/link";

export default function Home() {
  return (
    <div className="h-screen flex flex-col justify-center items-center text-center">
      <h1 className="text-4xl font-bold">
        Tamil Nadu NEET College Predictor
      </h1>

      <p className="mt-4 text-gray-600 text-lg">
        Enter your NEET marks and find probable MBBS colleges.
      </p>

      <Link href="/predictor">
        <button className="mt-6 bg-blue-600 text-white px-6 py-3 rounded-xl text-lg">
          Start Prediction
        </button>
      </Link>
    </div>
  );
}
