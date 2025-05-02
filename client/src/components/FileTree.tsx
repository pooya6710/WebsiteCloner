interface FileTreeItem {
  name: string;
  type: 'folder' | 'file';
  extension?: string;
  children?: FileTreeItem[];
}

interface FileTreeProps {
  structure: FileTreeItem[];
  level?: number;
}

const getFileIcon = (extension?: string) => {
  switch (extension) {
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
      return 'fas fa-file-code text-orange-400';
    case 'md':
      return 'fas fa-file-alt text-gray-500';
    case 'json':
      return 'fas fa-file text-gray-500';
    case 'html':
      return 'fas fa-file-code text-blue-400';
    case 'css':
    case 'scss':
    case 'sass':
      return 'fas fa-file-code text-purple-400';
    default:
      return 'fas fa-file text-gray-500';
  }
};

export default function FileTree({ structure, level = 0 }: FileTreeProps) {
  return (
    <ul className="space-y-1">
      {structure.map((item, index) => (
        <li 
          key={index} 
          className={`pl-${4 + level * 4} border-l-2 border-gray-200 hover:border-primary hover:bg-blue-50 rounded py-1 px-2 transition-colors duration-100`}
        >
          {item.type === 'folder' ? (
            <>
              <i className="fas fa-folder text-blue-400 mr-2"></i>
              {item.name}
              {item.children && item.children.length > 0 && (
                <FileTree structure={item.children} level={level + 1} />
              )}
            </>
          ) : (
            <>
              <i className={`${getFileIcon(item.extension)} mr-2`}></i>
              {item.name}
            </>
          )}
        </li>
      ))}
    </ul>
  );
}
