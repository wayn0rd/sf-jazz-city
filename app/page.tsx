"use client";

import React, { useState, useMemo, useEffect } from 'react';
import { Calendar, Clock, Music, Search } from 'lucide-react';
import { DisplayEvent } from './types/event';
import SiteHeader from './components/SiteHeader';
import SiteFooter from './components/SiteFooter';
import EventCard from './components/EventCard';
import { formatDate, formatFullDate } from './lib/format';

export default function SFJazzCity() {
  const [events, setEvents] = useState<DisplayEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState('all');

  // Get today's date in YYYY-MM-DD format
  const today = new Date().toISOString().split('T')[0];

  // Fetch events from API
  useEffect(() => {
    async function fetchEvents() {
      try {
        const response = await fetch('/api/events');
        const data = await response.json();
        setEvents(data.events || []);
      } catch (error) {
        console.error('Failed to fetch events:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchEvents();
  }, []);

  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      const matchesSearch = event.artist.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           event.venue.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesDate = selectedDate === 'all' || event.date === selectedDate;
      return matchesSearch && matchesDate;
    });
  }, [events, searchTerm, selectedDate]);

  const uniqueDates = useMemo(() => {
    const dates = Array.from(new Set(events.map(e => e.date))).sort();
    return ['all', ...dates];
  }, [events]);

  const todayEvents = useMemo(() => {
    return events.filter(e => e.date === today);
  }, [events, today]);

  // Full-screen loading state, deliberately unchanged: no site header here.
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Music className="w-16 h-16 text-amber-400 animate-pulse mx-auto mb-4" />
          <p className="text-white text-xl">Loading jazz events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <SiteHeader />

      {/* Hero Section */}
      <section className="relative py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-4">
            Tonight&apos;s SF Jazz
          </h2>
          <p className="text-xl text-amber-200 mb-8">
            Discover live jazz happening right now in San Francisco
          </p>
          <div className="flex justify-center items-center space-x-2 text-white/80">
            <Calendar className="w-5 h-5" />
            <span className="text-lg">{formatFullDate(today)}</span>
          </div>
        </div>
      </section>

      {/* Tonight's Featured Shows */}
      <section id="tonight" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <h3 className="text-3xl font-bold text-white mb-8 flex items-center">
          <Clock className="w-8 h-8 mr-3 text-amber-400" />
          Playing Tonight
        </h3>
        {todayEvents.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {todayEvents.map(event => (
              <EventCard key={event.id} event={event} variant="featured" />
            ))}
          </div>
        ) : (
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 text-center">
            <p className="text-white/70 text-lg">No shows scheduled for tonight. Check out upcoming events below!</p>
          </div>
        )}
      </section>

      {/* Search and Filter Section */}
      <section id="upcoming" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8">
        <h3 className="text-3xl font-bold text-white mb-8">Browse All Shows</h3>

        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 mb-8">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
              <input
                type="text"
                placeholder="Search artists or venues..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-amber-400"
              />
            </div>

            {/* Date Filter */}
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50 pointer-events-none" />
              <select
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-amber-400 appearance-none cursor-pointer"
              >
                {uniqueDates.map(date => (
                  <option key={date} value={date} className="bg-slate-900">
                    {formatDate(date)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Filtered Results */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEvents.map(event => (
            <EventCard key={event.id} event={event} variant="compact" />
          ))}
        </div>

        {filteredEvents.length === 0 && (
          <div className="text-center py-12">
            <p className="text-white/60 text-lg">No shows found. Try adjusting your filters.</p>
          </div>
        )}
      </section>

      <SiteFooter />
    </div>
  );
}
