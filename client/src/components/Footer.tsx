export default function Footer() {
  return (
    <footer className="bg-dark-lighter text-white py-4">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center mb-4 md:mb-0">
            <i className="fas fa-code-branch text-primary mr-2"></i>
            <span>DevClone &copy; {new Date().getFullYear()}</span>
          </div>
          <div className="flex space-x-4">
            <a href="#" className="text-gray-400 hover:text-white transition duration-200">Documentation</a>
            <a href="#" className="text-gray-400 hover:text-white transition duration-200">Support</a>
            <a href="#" className="text-gray-400 hover:text-white transition duration-200">Privacy Policy</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
