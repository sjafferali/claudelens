import { Search as SearchIcon } from 'lucide-react';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';

export default function Search() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Search</h2>
        <p className="text-muted-foreground">
          Search through all your Claude conversations
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Conversations</CardTitle>
          <CardDescription>
            Find messages, code snippets, or specific topics across all your
            sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4">
            <div className="flex gap-4">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search for messages, code, or topics..."
                  className="pl-10 pr-4 py-2 w-full bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <Button type="submit">Search</Button>
            </div>

            <div className="flex gap-4 flex-wrap">
              <select className="px-3 py-2 bg-background border border-input rounded-md">
                <option value="">All Projects</option>
                <option value="project1">Project 1</option>
                <option value="project2">Project 2</option>
              </select>

              <select className="px-3 py-2 bg-background border border-input rounded-md">
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </select>

              <select className="px-3 py-2 bg-background border border-input rounded-md">
                <option value="">All Models</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                <option value="claude-3-haiku">Claude 3 Haiku</option>
              </select>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Search Results</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            Enter a search query to find conversations
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
