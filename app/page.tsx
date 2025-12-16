"use client";

import React, { useState, useMemo } from 'react';
import { Calendar, MapPin, Clock, Music, Search, Filter, ExternalLink } from 'lucide-react';

// Sample data - in production this would come from your database
const sampleEvents = [
  {
    id: 1,
    artist: "Marcus Shelby Quartet",
    venue: "SFJAZZ Center",
    date: "2025-11-26",
    time: "19:30",
    price: "$35-55",
    style: "Modern Jazz",
    description: "Bay Area legend Marcus Shelby brings his signature blend of composition and improvisation.",
    ticketUrl: "#",
    image: "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=400&h=300&fit=crop"
  },
  {
    id: 2,
    artist: "Lavay Smith & Her Red Hot Skillet Lickers",
    venue: "The Black Cat",
    date: "2025-11-26",
    time: "20:00",
    price: "$25",
    style: "Swing",
    description: "High-energy swing and jump blues with SF's own Queen of Classic Jazz.",
    ticketUrl: "#",
    image: "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?w=400&h=300&fit=crop"
  },
  {
    id: 3,
    artist: "Ben Goldberg Trio",
    venue: "Yoshi's Oakland",
    date: "2025-11-26",
    time: "20:00",
    price: "$30-40",
    style: "Avant-Garde",
    description: "Experimental clarinet master explores new sonic territories.",
    ticketUrl: "#",
    image: "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=400&h=300&fit=crop"
  },
  {
    id: 4,
    artist: "Jazz at Lincoln Center Orchestra",
    venue: "SFJAZZ Center",
    date: "2025-11-27",
    time: "19:30",
    price: "$65-125",
    style: "Big Band",
    description: "Wynton Marsalis leads this legendary ensemble in an evening of swing classics.",
    ticketUrl: "#",
    image: "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=400&h=300&fit=crop"
  },
  {
    id: 5,
    artist: "Tiffany Austin",
    venue: "Bird & Beckett",
    date: "2025-11-27",
    time: "19:00",
    price: "$20",
    style: "Vocal Jazz",
    description: "Intimate evening with one of the Bay Area's most captivating vocalists.",
    ticketUrl: "#",
    image: "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=300&fit=crop"
  },
  {
    id: 6,
    artist: "Ambrose Akinmusire Quartet",
    venue: "The Chapel",
    date: "2025-11-28",
    time: "21:00",
    price: "$40",
    style: "Modern Jazz",
    description: "Grammy-nominated trumpeter pushes the boundaries of contemporary jazz.",
    ticketUrl: "#",
    image: "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?w=400&h=300&fit=crop"
  }
];

const venues = [
  { name: "SFJAZZ Center", neighborhood: "Hayes Valley" },
  { name: "Yoshi's Oakland", neighborhood: "Oakland" },
  { name: "The Black Cat", neighborhood: "Tenderloin" },
  { name: "Bird & Beckett", neighborhood: "Glen Park" },
  { name: "The Chapel", neighborhood: "Mission" }
];

export default function SFJazzCity() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState('2025-11-26');
  const [selectedStyle, setSelectedStyle] = useState('all');

  const styles = ['all', ...new Set(sampleEvents.map(e => e.style))];

  const filteredEvents = useMemo(() => {
    return sampleEvents.filter(event => {
      const matchesSearch = event.artist.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           event.venue.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesDate = selectedDate === 'all' || event.date === selectedDate;
      const matchesStyle = selectedStyle === 'all' || event.style === selectedStyle;
      return matchesSearch && matchesDate && matchesStyle;
    });
  }, [searchTerm, selectedDate, selectedStyle]);

  const uniqueDates = ['all', ...new Set(sampleEvents.map(e => e.date))];

  const formatDate = (dateStr) => {
    if (dateStr === 'all') return 'All Dates';
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const todayEvents = sampleEvents.filter(e => e.date === '2025-11-26');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Music className="w-8 h-8 text-amber-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">SF Jazz City</h1>
                <p className="text-xs text-amber-400">Your Guide to San Francisco Jazz</p>
              </div>
            </div>
            <nav className="hidden md:flex space-x-6 text-sm">
              <a href="#tonight" className="text-white hover:text-amber-400 transition">Tonight</a>
              <a href="#upcoming" className="text-white hover:text-amber-400 transition">Upcoming</a>
              <a href="#venues" className="text-white hover:text-amber-400 transition">Venues</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-4">
            Tonight's Jazz Scene
          </h2>
          <p className="text-xl text-amber-200 mb-8">
            Discover live jazz happening right now in San Francisco
          </p>
          <div className="flex justify-center items-center space-x-2 text-white/80">
            <Calendar className="w-5 h-5" />
            <span className="text-lg">Wednesday, November 26, 2025</span>
          </div>
        </div>
      </section>

      {/* Tonight's Featured Shows */}
      <section id="tonight" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <h3 className="text-3xl font-bold text-white mb-8 flex items-center">
          <Clock className="w-8 h-8 mr-3 text-amber-400" />
          Playing Tonight
        </h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {todayEvents.map(event => (
            <div key={event.id} className="bg-white/10 backdrop-blur-sm rounded-xl overflow-hidden border border-white/20 hover:border-amber-400/50 transition-all hover:scale-105 hover:shadow-2xl hover:shadow-amber-500/20">
              <img src={event.image} alt={event.artist} className="w-full h-48 object-cover" />
              <div className="p-6">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="text-xl font-bold text-white">{event.artist}</h4>
                  <span className="text-xs bg-amber-500 text-black px-2 py-1 rounded-full font-semibold">
                    {event.style}
                  </span>
                </div>
                <div className="space-y-2 text-sm text-white/80 mb-4">
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-2 text-amber-400" />
                    {event.venue}
                  </div>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-2 text-amber-400" />
                    {event.time} · {event.price}
                  </div>
                </div>
                <p className="text-white/70 text-sm mb-4">{event.description}</p>
                <a
                  href={event.ticketUrl}
                  className="inline-flex items-center justify-center w-full bg-amber-500 hover:bg-amber-400 text-black font-semibold py-2 px-4 rounded-lg transition"
                >
                  Get Tickets
                  <ExternalLink className="w-4 h-4 ml-2" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Search and Filter Section */}
      <section id="upcoming" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8">
        <h3 className="text-3xl font-bold text-white mb-8">Browse All Shows</h3>
        
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 mb-8">
          <div className="grid md:grid-cols-3 gap-4">
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
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
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

            {/* Style Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
              <select
                value={selectedStyle}
                onChange={(e) => setSelectedStyle(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-amber-400 appearance-none cursor-pointer"
              >
                {styles.map(style => (
                  <option key={style} value={style} className="bg-slate-900">
                    {style === 'all' ? 'All Styles' : style}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Filtered Results */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEvents.map(event => (
            <div key={event.id} className="bg-white/10 backdrop-blur-sm rounded-xl overflow-hidden border border-white/20 hover:border-amber-400/50 transition-all hover:scale-105">
              <img src={event.image} alt={event.artist} className="w-full h-40 object-cover" />
              <div className="p-5">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-lg font-bold text-white">{event.artist}</h4>
                  <span className="text-xs bg-amber-500 text-black px-2 py-1 rounded-full font-semibold">
                    {event.style}
                  </span>
                </div>
                <div className="space-y-1 text-sm text-white/80 mb-3">
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-2 text-amber-400" />
                    {event.venue}
                  </div>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-2 text-amber-400" />
                    {formatDate(event.date)} · {event.time}
                  </div>
                </div>
                <a
                  href={event.ticketUrl}
                  className="inline-flex items-center justify-center w-full bg-amber-500 hover:bg-amber-400 text-black font-semibold py-2 px-4 rounded-lg transition text-sm"
                >
                  Get Tickets
                  <ExternalLink className="w-4 h-4 ml-2" />
                </a>
              </div>
            </div>
          ))}
        </div>

        {filteredEvents.length === 0 && (
          <div className="text-center py-12">
            <p className="text-white/60 text-lg">No shows found. Try adjusting your filters.</p>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="bg-black/30 backdrop-blur-md border-t border-white/10 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-white/60 text-sm">
            <p className="mb-2">© 2025 SF Jazz City. Your guide to live jazz in San Francisco.</p>
            <p className="text-xs">Event data updated daily. Always verify details with venues.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
