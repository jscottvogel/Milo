"use client";

import { useEffect, useState } from "react";
import { Mail, Calendar as CalendarIcon, Clock, Users, ArrowRight } from "lucide-react";
import { fetchEmails, fetchMeetings } from "@/lib/api";

export default function InboxPage() {
  const [emails, setEmails] = useState<any[]>([]);
  const [meetings, setMeetings] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadInbox = async () => {
      try {
        const [emailsData, meetingsData] = await Promise.all([
          fetchEmails(),
          fetchMeetings()
        ]);
        setEmails(emailsData || []);
        setMeetings(meetingsData || []);
      } catch (err) {
        console.error("Failed to load inbox data", err);
      } finally {
        setIsLoading(false);
      }
    };
    loadInbox();
  }, []);

  return (
    <div className="p-6 h-full flex flex-col gap-8 overflow-y-auto custom-scrollbar">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Unified Inbox</h1>
        <p className="text-muted-foreground">Manage your communications and schedule, integrated directly with Milo.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Emails Section */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Mail className="w-5 h-5 text-blue-400" />
            Recent Communications
          </h2>
          
          <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden flex flex-col h-[500px]">
            <div className="p-4 border-b border-white/10 bg-[#0a0a0c]">
              <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wider">Unread Mail</h3>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
              {isLoading ? (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  Loading communications...
                </div>
              ) : emails.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 text-muted-foreground">
                  <Mail className="w-12 h-12 mb-4 text-white/5" />
                  <p>Your inbox is empty or not connected to Nylas.</p>
                  <p className="text-xs mt-2">Connect your account in Settings to see live emails.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {emails.map((email: any) => (
                    <div key={email.id} className="p-4 rounded-lg hover:bg-white/5 cursor-pointer transition-colors border border-transparent hover:border-white/10 group">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-white truncate pr-4">{email.sender}</span>
                        <span className="text-xs text-muted-foreground shrink-0">{email.time}</span>
                      </div>
                      <h4 className="text-sm font-medium text-white/90 truncate mb-1">{email.subject}</h4>
                      <p className="text-xs text-muted-foreground line-clamp-2">{email.preview}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Meetings Section */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <CalendarIcon className="w-5 h-5 text-purple-400" />
            Upcoming Schedule
          </h2>
          
          <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden flex flex-col h-[500px]">
            <div className="p-4 border-b border-white/10 bg-[#0a0a0c]">
              <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wider">Next 7 Days</h3>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
              {isLoading ? (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  Loading schedule...
                </div>
              ) : meetings.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 text-muted-foreground">
                  <CalendarIcon className="w-12 h-12 mb-4 text-white/5" />
                  <p>No upcoming meetings found.</p>
                  <p className="text-xs mt-2">Connect your calendar in Settings to sync events.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {meetings.map((meeting: any) => (
                    <div key={meeting.id} className="p-4 rounded-lg bg-white/5 border border-white/5 hover:border-white/10 transition-colors flex flex-col gap-3">
                      <div className="flex justify-between items-start">
                        <h4 className="font-medium text-white line-clamp-2">{meeting.title}</h4>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground mt-auto">
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          {meeting.time}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5" />
                          {meeting.attendees} attendees
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
