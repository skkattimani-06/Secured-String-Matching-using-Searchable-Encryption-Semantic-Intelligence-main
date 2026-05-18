import { useState, useEffect } from "react";
import { deriveKey } from "./services/api";
import UploadCard from "./components/UploadCard";
import SearchCard from "./components/SearchCard";

function App() {
  const [secretKey, setSecretKey] = useState<CryptoKey | null>(null);

  useEffect(() => {
    deriveKey("password123").then(setSecretKey);
  }, []);

  if (!secretKey) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-gray-500 text-sm">Initializing secure session...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 px-6 py-10">

      {/* Heading */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-black tracking-tight">
          Secured String Matching
        </h1>
        <p className="text-gray-500 mt-2 text-sm">
          using Searchable Encryption + Semantic Intelligence
        </p>
      </div>

      {/* Cards */}
      <div className="max-w-2xl mx-auto space-y-6">
        <UploadCard />
        <SearchCard secretKey={secretKey} />
      </div>

    </div>
  );
}

export default App;