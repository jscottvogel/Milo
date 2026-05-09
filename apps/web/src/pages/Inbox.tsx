import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Video, Send, FilePlus, Users, Calendar, Sparkles } from 'lucide-react';
import clsx from 'clsx';

export const Inbox: React.FC = () => {
  const { setBreadcrumbContext } = useAppStore();
  const [activeTab, setActiveTab] = useState<'emails' | 'meetings'>('emails');

  useEffect(() => {
    setBreadcrumbContext([{ label: 'Inbox', path: '/inbox' }]);
  }, [setBreadcrumbContext]);

  // TODO: MOCK - Email endpoint not available yet in Milo backend
  const emails = [
    {
      id: 1,
      sender: 'alex.chen@vendor.com',
      subject: 'Re: Enterprise Contract Revision',
      snippet: 'Hi there, we reviewed the redlines and accept 90% of the terms, but...',
      date: '10:45 AM',
      unread: true,
      draft: 'Hi Alex, thanks for the quick turnaround. Could you clarify which 10% remains an issue? We can jump on a call if easier.\n\nBest,\nMilo (on behalf of JS)'
    },
    {
      id: 2,
      sender: 'sarah.k@internal.org',
      subject: 'Project X - Weekly Status',
      snippet: 'Status is green across the board. The only minor risk is...',
      date: 'Yesterday',
      unread: false,
    }
  ];

  // TODO: MOCK - Meetings/Transcript endpoint not available yet in Milo backend
  const meetings = [
    {
      id: 1,
      title: 'Q3 Objectives Sync',
      date: 'Today, 9:00 AM',
      attendees: ['JS', 'AL', 'TK'],
      summary: 'Discussed the slip in the Q3 objective. Agreed to reallocate engineering resources to unblock the marketing rollout. Alex to draft new timeline.',
      actionItems: [
        { text: 'Reallocate 2 engineers to Team B', owner: 'JS', linked: false },
        { text: 'Draft new rollout timeline', owner: 'Alex', linked: true }
      ]
    }
  ];

  return (
    <div className="flex flex-col h-full bg-background max-w-6xl mx-auto">
      {/* Header & Tabs */}
      <div className="sticky top-0 z-10 bg-[#0a0a0c]/90 backdrop-blur-md px-6 sm:px-8 pt-6 pb-0 border-b border-border flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-6">Unified Inbox</h1>
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('emails')}
              className={clsx(
                "pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2",
                activeTab === 'emails' ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-white"
              )}
            >
              <Mail className="w-4 h-4" />
              Emails
              <span className="ml-1 bg-primary text-primary-foreground text-[10px] px-1.5 py-0.5 rounded-full">1</span>
            </button>
            <button
              onClick={() => setActiveTab('meetings')}
              className={clsx(
                "pb-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2",
                activeTab === 'meetings' ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-white"
              )}
            >
              <Video className="w-4 h-4" />
              Meeting Notes
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6">
        <AnimatePresence mode="wait">
          
          {activeTab === 'emails' && (
            <motion.div
              key="emails"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {emails.map(email => (
                <div key={email.id} className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden group">
                  <div className="p-5">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        {email.unread && <div className="w-2 h-2 rounded-full bg-primary" />}
                        <h3 className={clsx("font-medium", email.unread ? "text-white" : "text-gray-300")}>
                          {email.sender}
                        </h3>
                      </div>
                      <span className="text-xs text-muted-foreground">{email.date}</span>
                    </div>
                    <h4 className="text-sm font-semibold mb-1">{email.subject}</h4>
                    <p className="text-sm text-muted-foreground line-clamp-2">{email.snippet}</p>
                    
                    <div className="mt-4 flex gap-2">
                      <button className="text-xs flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-md transition-colors text-muted-foreground hover:text-white border border-white/5">
                        <FilePlus className="w-3.5 h-3.5" />
                        Create Work Item
                      </button>
                    </div>
                  </div>

                  {email.draft && (
                    <div className="bg-primary/5 border-t border-primary/10 p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="w-4 h-4 text-primary" />
                        <span className="text-xs font-semibold text-primary uppercase tracking-wide">Milo Drafted Reply</span>
                      </div>
                      <textarea 
                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-gray-300 min-h-[100px] outline-none focus:border-primary/50 transition-colors"
                        defaultValue={email.draft}
                      />
                      <div className="flex justify-end gap-2 mt-3">
                        <button className="text-sm px-4 py-2 hover:bg-white/5 rounded-md transition-colors text-muted-foreground">
                          Discard
                        </button>
                        <button className="text-sm px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md transition-colors flex items-center gap-2">
                          <Send className="w-4 h-4" /> Send Reply
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </motion.div>
          )}

          {activeTab === 'meetings' && (
            <motion.div
              key="meetings"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {meetings.map(meeting => (
                <div key={meeting.id} className="bg-[#111115] border border-white/10 rounded-xl p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-bold text-white">{meeting.title}</h3>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded">
                      <Calendar className="w-3.5 h-3.5" />
                      {meeting.date}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 mb-4 text-sm text-muted-foreground">
                    <Users className="w-4 h-4" />
                    <span>Attendees: {meeting.attendees.join(', ')}</span>
                  </div>

                  <div className="mb-6">
                    <h4 className="text-sm font-semibold mb-2">Transcript Summary</h4>
                    <p className="text-sm text-gray-300 leading-relaxed bg-white/5 p-4 rounded-lg border border-white/5">
                      {meeting.summary}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary" />
                      Extracted Action Items
                    </h4>
                    <ul className="space-y-2">
                      {meeting.actionItems.map((ai, i) => (
                        <li key={i} className="flex items-center justify-between text-sm bg-black/20 p-3 rounded-lg border border-white/5">
                          <div className="flex items-center gap-3">
                            <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[9px] font-bold">
                              {ai.owner.substring(0,2).toUpperCase()}
                            </div>
                            <span className="text-gray-300">{ai.text}</span>
                          </div>
                          {ai.linked ? (
                            <span className="text-[10px] text-green-400 bg-green-500/10 px-2 py-1 rounded border border-green-500/20">Linked</span>
                          ) : (
                            <button className="text-[10px] text-primary hover:bg-primary/10 px-2 py-1 rounded transition-colors border border-transparent hover:border-primary/20">
                              Convert to Task
                            </button>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
};

export default Inbox;
