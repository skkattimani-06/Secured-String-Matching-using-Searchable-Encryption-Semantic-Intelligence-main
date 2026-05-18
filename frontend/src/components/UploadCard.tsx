import { useState } from "react";
import { uploadDocument } from "../services/api";

const UploadCard = () => {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a document before uploading.");
      return;
    }
    try {
      await uploadDocument(file);
      setMessage("Document encrypted and stored successfully.");
    } catch {
      setMessage("Upload failed. Please try again.");
    }
  };

  return (
    <div className="bg-white shadow-2xl rounded-2xl p-8">
      <h2 className="text-xl font-semibold mb-4">Upload Document</h2>

      <div className="border-2 border-dashed border-gray-300 rounded-xl 
                      p-6 hover:border-black transition">
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => {
            if (e.target.files) setFile(e.target.files[0]);
          }}
          className="block w-full text-sm text-gray-600
            file:mr-4 file:py-2 file:px-6
            file:rounded-lg file:border-0
            file:text-sm file:font-medium
            file:bg-black file:text-white
            hover:file:bg-gray-800 cursor-pointer"
        />
      </div>

      <button
        onClick={handleUpload}
        className="w-full mt-5 bg-black text-white py-3 rounded-xl 
                   font-medium hover:bg-gray-900 transition"
      >
        Upload Document
      </button>

      {message && (
        <p className="text-center text-gray-600 text-sm mt-4">{message}</p>
      )}
    </div>
  );
};

export default UploadCard;