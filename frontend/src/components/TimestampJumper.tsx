import { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { format, isValid, parse } from 'date-fns';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';

interface TimestampJumperProps {
  messages: Message[];
  onJumpToMessage: (messageId: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function TimestampJumper({
  messages,
  onJumpToMessage,
  isOpen,
  onClose,
}: TimestampJumperProps) {
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedDate, setSelectedDate] = useState(
    format(new Date(), 'yyyy-MM-dd')
  );

  const handleJump = () => {
    if (!selectedTime) return;

    const targetDateTime = parse(
      `${selectedDate} ${selectedTime}`,
      'yyyy-MM-dd HH:mm',
      new Date()
    );

    if (!isValid(targetDateTime)) return;

    // Find the closest message to the target time
    let closestMessage = messages[0];
    let closestDiff = Math.abs(
      new Date(messages[0].timestamp).getTime() - targetDateTime.getTime()
    );

    for (const message of messages) {
      const messageDiff = Math.abs(
        new Date(message.timestamp).getTime() - targetDateTime.getTime()
      );
      if (messageDiff < closestDiff) {
        closestDiff = messageDiff;
        closestMessage = message;
      }
    }

    if (closestMessage) {
      onJumpToMessage(closestMessage._id);
      onClose();
    }
  };

  if (!isOpen || messages.length === 0) return null;

  const firstMessageDate = new Date(messages[0].timestamp);
  const lastMessageDate = new Date(messages[messages.length - 1].timestamp);

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-xl border border-gray-200 dark:border-slate-600 p-4 animate-in fade-in slide-in-from-top-2 duration-200">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-5 w-5 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Jump to Timestamp
          </h3>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
              Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={format(firstMessageDate, 'yyyy-MM-dd')}
              max={format(lastMessageDate, 'yyyy-MM-dd')}
              className={cn(
                'w-full px-3 py-2 border rounded-md',
                'bg-white dark:bg-slate-900',
                'border-gray-300 dark:border-slate-600',
                'text-gray-900 dark:text-gray-100',
                'focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              )}
            />
          </div>

          <div>
            <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
              Time
            </label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="time"
                value={selectedTime}
                onChange={(e) => setSelectedTime(e.target.value)}
                className={cn(
                  'w-full pl-10 pr-3 py-2 border rounded-md',
                  'bg-white dark:bg-slate-900',
                  'border-gray-300 dark:border-slate-600',
                  'text-gray-900 dark:text-gray-100',
                  'focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                )}
                placeholder="HH:MM"
              />
            </div>
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-400">
            Session range: {format(firstMessageDate, 'MMM d, HH:mm')} -{' '}
            {format(lastMessageDate, 'MMM d, HH:mm')}
          </div>

          <div className="flex gap-2 pt-2">
            <button
              onClick={handleJump}
              disabled={!selectedTime}
              className={cn(
                'flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                'bg-blue-600 text-white hover:bg-blue-700',
                'disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed'
              )}
            >
              Jump to Time
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
