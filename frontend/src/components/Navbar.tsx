const Navbar = () => {
  return (
    <nav className="bg-black text-white py-4 shadow-md">
      <div className="max-w-6xl mx-auto px-6 flex justify-between items-center">
        <h1 className="text-lg font-semibold tracking-wide">
          Secure Semantic Search
        </h1>

        <span className="text-sm text-gray-400">
          Encrypted Document Retrieval
        </span>
      </div>
    </nav>
  );
};

export default Navbar;