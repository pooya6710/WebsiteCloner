import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";

const navigation = [
  { name: 'Dashboard', href: '/', icon: 'fas fa-home' },
  { name: 'Repositories', href: '/repositories', icon: 'fas fa-code-branch' },
  { name: 'Projects', href: '/projects', icon: 'fas fa-tasks' },
  { name: 'Environments', href: '/environments', icon: 'fas fa-cube' },
  { name: 'Deployments', href: '/deployments', icon: 'fas fa-rocket' },
];

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: 'fas fa-cog' },
  { name: 'Help & Support', href: '/help', icon: 'fas fa-question-circle' },
];

export default function Sidebar() {
  const [location] = useLocation();

  return (
    <aside className="bg-dark-lighter text-white w-64 p-4">
      <nav>
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = location === item.href;
            return (
              <li key={item.name}>
                <Link href={item.href}>
                  <a className={cn(
                    "flex items-center space-x-3 p-3 rounded-md transition duration-200",
                    isActive 
                      ? "bg-primary bg-opacity-20 border-l-4 border-primary" 
                      : "hover:bg-primary hover:bg-opacity-10"
                  )}>
                    <i className={item.icon}></i>
                    <span>{item.name}</span>
                  </a>
                </Link>
              </li>
            );
          })}
          
          <li className="pt-4 border-t border-gray-600 mt-4">
            {secondaryNavigation.map((item) => (
              <Link href={item.href} key={item.name}>
                <a className="flex items-center space-x-3 p-3 rounded-md hover:bg-primary hover:bg-opacity-10 transition duration-200">
                  <i className={item.icon}></i>
                  <span>{item.name}</span>
                </a>
              </Link>
            ))}
          </li>
        </ul>
      </nav>
    </aside>
  );
}
