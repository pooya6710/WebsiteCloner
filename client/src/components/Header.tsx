import { useState } from "react";
import { Link } from "wouter";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Plus, ChevronDown } from "lucide-react";
import { useMobile } from "@/hooks/use-mobile";
import Sidebar from "./Sidebar";

export default function Header() {
  const isMobile = useMobile();
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  return (
    <header className="bg-dark text-white shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Link href="/" className="flex items-center space-x-2">
            <svg className="h-6 w-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7 18v-2m3-1v3m3-4v4m3-5v5" />
              <path d="M4 21h16a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1z" />
            </svg>
            <h1 className="text-xl font-bold">DevClone</h1>
          </Link>
        </div>

        <div className="flex items-center space-x-4">
          <Button onClick={() => window.location.href = '/new-project'} className="bg-primary hover:bg-blue-600 text-white">
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center space-x-2 outline-none">
              <div className="h-8 w-8 rounded-full bg-gray-400 flex items-center justify-center overflow-hidden">
                <img src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=120&q=80" 
                  alt="User" 
                  className="h-full w-full object-cover"
                />
              </div>
              <span className="hidden md:inline">Developer</span>
              <ChevronDown className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuItem>Logout</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {isMobile && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="text-white"
            >
              <svg
                strokeWidth="1.5"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
              >
                <path
                  d="M3 5H21"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                ></path>
                <path
                  d="M3 12H21"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                ></path>
                <path
                  d="M3 19H21"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                ></path>
              </svg>
            </Button>
          )}
        </div>
      </div>
      
      {isMobile && showMobileMenu && (
        <div className="md:hidden">
          <Sidebar />
        </div>
      )}
    </header>
  );
}
