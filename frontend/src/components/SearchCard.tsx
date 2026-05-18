import { useState } from "react";
import { searchDocuments } from "../services/api";
import type { SearchResult } from "../types";

interface Props {
  secretKey: CryptoKey;
}

const SearchCard = ({ secretKey }: Props) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query) {
      setMessage("Please enter a search query.");
      return;
    }
    try {
      setLoading(true);
      setMessage("");
      const data = await searchDocuments(query, secretKey);
      setResults(data.results ?? []);
      if ((data.results ?? []).length === 0) {
        setMessage("No results found.");
      }
    } catch {
      setMessage("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-2xl rounded-2xl p-8">
      <h2 className="text-xl font-semibold mb-4">Semantic Search</h2>

      <div className="flex gap-3">
        <input
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3
                     focus:outline-none focus:ring-2 focus:ring-black"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter secure search query..."
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-black text-white px-6 py-3 rounded-xl
                     hover:bg-gray-900 transition disabled:opacity-50"
        >
          {loading ? "Searching..." : "Execute Search"}
        </button>
      </div>

      {message && (
        <p className="text-center text-gray-500 text-sm mt-4">{message}</p>
      )}

      <div className="mt-6">
        {results.length === 0 && !message ? (
          <p className="text-center text-gray-400 text-sm">
            No results yet. Try searching something.
          </p>
        ) : (
          results.map((doc) => (
            <div
              key={doc.doc_id}
              className="bg-gray-50 border border-gray-200
                         rounded-xl p-4 mb-4"
            >
              <p className="text-sm text-gray-500">
                Similarity Score:{" "}
                <span className="font-medium text-black">
                  {(doc.score * 100).toFixed(1)}%
                </span>
              </p>
              <p className="mt-2 text-gray-800 text-sm leading-relaxed">
                {doc.content}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default SearchCard;