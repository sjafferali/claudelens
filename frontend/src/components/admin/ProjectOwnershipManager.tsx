import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  ArrowRight,
  User,
  Folder,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/common/Button';
import toast from 'react-hot-toast';
import { apiClient } from '@/api/client';

interface ProjectOwner {
  _id: string;
  username: string;
  email: string;
}

interface ProjectWithOwner {
  _id: string;
  name: string;
  path: string;
  createdAt: string;
  updatedAt: string;
  stats: {
    message_count: number;
    session_count: number;
  };
  owner?: ProjectOwner;
}

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

export const ProjectOwnershipManager: React.FC = () => {
  const [projects, setProjects] = useState<ProjectWithOwner[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProject, setSelectedProject] =
    useState<ProjectWithOwner | null>(null);
  const [selectedNewOwner, setSelectedNewOwner] = useState<string>('');
  const [transferring, setTransferring] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const itemsPerPage = 10;

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<{
        data: {
          items: ProjectWithOwner[];
          total: number;
        };
      }>(
        `/admin/projects/with-owners?skip=${(currentPage - 1) * itemsPerPage}&limit=${itemsPerPage}`
      );
      setProjects(response.data.items);
      setTotalPages(Math.ceil(response.data.total / itemsPerPage));
    } catch (error) {
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, [currentPage, itemsPerPage]);

  useEffect(() => {
    loadProjects();
    loadUsers();
  }, [currentPage, loadProjects]);

  const loadUsers = async () => {
    try {
      const response = await apiClient.get<{
        data: {
          items: User[];
        };
      }>('/users');
      setUsers(response.data.items);
    } catch (error) {
      toast.error('Failed to load users');
    }
  };

  const handleTransferOwnership = async () => {
    if (!selectedProject || !selectedNewOwner) return;

    setTransferring(true);
    try {
      await apiClient.post('/admin/projects/transfer-ownership', {
        project_id: selectedProject._id,
        new_owner_id: selectedNewOwner,
      });

      toast.success('Project ownership transferred successfully');

      // Reload projects to reflect changes
      await loadProjects();
      setSelectedProject(null);
      setSelectedNewOwner('');
    } catch (error) {
      toast.error('Failed to transfer project ownership');
    } finally {
      setTransferring(false);
    }
  };

  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.owner?.username
        .toLowerCase()
        .includes(searchTerm.toLowerCase()) ||
      project.owner?.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Project Ownership Management
          </h2>
          <Button
            onClick={loadProjects}
            variant="outline"
            size="sm"
            disabled={loading}
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
        </div>

        {/* Search Bar */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by project name, path, or owner..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        {/* Projects Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b dark:border-gray-700">
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                  Project
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                  Path
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                  Current Owner
                </th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                  Stats
                </th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-500">
                    Loading projects...
                  </td>
                </tr>
              ) : filteredProjects.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-500">
                    No projects found
                  </td>
                </tr>
              ) : (
                filteredProjects.map((project) => (
                  <tr
                    key={project._id}
                    className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        <Folder className="w-5 h-5 text-gray-400 mr-2" />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {project.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            ID: {project._id}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <p className="text-sm text-gray-600 dark:text-gray-400 font-mono truncate max-w-xs">
                        {project.path}
                      </p>
                    </td>
                    <td className="py-3 px-4">
                      {project.owner ? (
                        <div className="flex items-center">
                          <User className="w-4 h-4 text-gray-400 mr-2" />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {project.owner.username}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {project.owner.email}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-red-500">No owner</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        <p>{project.stats.session_count} sessions</p>
                        <p>{project.stats.message_count} messages</p>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Button
                        onClick={() => setSelectedProject(project)}
                        variant="outline"
                        size="sm"
                      >
                        Transfer
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Page {currentPage} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              onClick={() =>
                setCurrentPage(Math.min(totalPages, currentPage + 1))
              }
              variant="outline"
              size="sm"
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Transfer Ownership Modal */}
      {selectedProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Transfer Project Ownership
            </h3>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Project:
                </p>
                <div className="p-3 bg-gray-100 dark:bg-gray-900 rounded-lg">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {selectedProject.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {selectedProject.path}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Current Owner:
                </p>
                <div className="p-3 bg-gray-100 dark:bg-gray-900 rounded-lg flex items-center">
                  <User className="w-4 h-4 text-gray-400 mr-2" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {selectedProject.owner?.username || 'No owner'}
                    </p>
                    {selectedProject.owner && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {selectedProject.owner.email}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400" />
              </div>

              <div>
                <label
                  htmlFor="new-owner"
                  className="block text-sm text-gray-600 dark:text-gray-400 mb-2"
                >
                  Transfer To:
                </label>
                <select
                  id="new-owner"
                  value={selectedNewOwner}
                  onChange={(e) => setSelectedNewOwner(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Select a user</option>
                  {users
                    .filter((u) => u.id !== selectedProject.owner?._id)
                    .map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.username} ({user.email}) - {user.role}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <Button
                onClick={() => {
                  setSelectedProject(null);
                  setSelectedNewOwner('');
                }}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={handleTransferOwnership}
                variant="default"
                disabled={!selectedNewOwner || transferring}
                className="flex-1"
              >
                {transferring ? 'Transferring...' : 'Transfer Ownership'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
