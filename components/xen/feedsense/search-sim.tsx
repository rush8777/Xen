'use client'

import React, { useState } from 'react'
import { 
  Search,
  MessageCircle,
  FileText,
  Scissors,
  Megaphone,
  Cpu

 } from 'lucide-react'
 import { cn } from "@/lib/utils"


const InstagramPostShowcase = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTopTab, setActiveTopTab] = useState('video-chat')

  const posts = [
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'HELLO\nCREATORS,\nGOODBYE\nCHAOS!',
      subtext: 'Best analytics\nfor content',
      gradient: 'from-primary via-purple-600 to-primary'
    },
    {
      brand: 'Vesko AI',
      tagline: 'Promoted',
      headline: 'TRACK\nSMART,\nGROW\nFAST!',
      subtext: 'AI-powered\ninsights',
      gradient: 'from-emerald-500 via-teal-600 to-emerald-500'
    },
    {
      brand: 'Vesko Pro',
      tagline: 'Promoted',
      headline: 'DATA\nMEETS\nCREATIVITY!',
      subtext: 'Unify your\nplatforms',
      gradient: 'from-yellow-500 via-orange-600 to-yellow-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'INSIGHTS\nTHAT\nMATTER!',
      subtext: 'Deep analytics\nmade simple',
      gradient: 'from-blue-500 via-indigo-600 to-blue-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'CONTENT\nFIRST,\nALWAYS!',
      subtext: 'Creator-focused\ntools',
      gradient: 'from-pink-500 via-rose-600 to-pink-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'AUTOMATE\nYOUR\nSUCCESS!',
      subtext: 'Smart workflows\nfor creators',
      gradient: 'from-cyan-500 via-sky-600 to-cyan-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'VIRAL\nSTARTS\nHERE!',
      subtext: 'Predict what\nworks',
      gradient: 'from-violet-500 via-purple-600 to-violet-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'KNOW\nYOUR\nAUDIENCE!',
      subtext: 'Deep sentiment\nanalysis',
      gradient: 'from-green-500 via-emerald-600 to-green-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'ONE\nDASH,\nALL DATA!',
      subtext: 'Unified content\nview',
      gradient: 'from-red-500 via-orange-600 to-red-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'SCALE\nWITH\nCONFIDENCE!',
      subtext: 'Enterprise-grade\ntools',
      gradient: 'from-amber-500 via-yellow-600 to-amber-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'TRENDS\nBEFORE\nTHEY HIT!',
      subtext: 'Predictive\nanalytics',
      gradient: 'from-teal-500 via-cyan-600 to-teal-500'
    },
    {
      brand: 'Vesko',
      tagline: 'Promoted',
      headline: 'CREATE\nSMARTER,\nNOT HARDER!',
      subtext: 'AI assists\nyour creativity',
      gradient: 'from-fuchsia-500 via-pink-600 to-fuchsia-500'
    }
  ]

  // Filter posts based on search query
  const filteredPosts = posts.filter(post => 
    post.brand.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.headline.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.subtext.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-[#0a0a0a]">
      <div className="max-w-7xl mx-auto">

        {/* Search Bar */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <input
              type="text"
              placeholder="Search posts by brand, headline, or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-card border border-border rounded-lg pl-12 pr-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 8.586L6.707 5.293a1 1 0 00-1.414 1.414L8.586 10l-3.293 3.293a1 1 0 101.414 1.414L10 11.414l3.293 3.293a1 1 0 001.414-1.414L11.414 10l3.293-3.293a1 1 0 00-1.414-1.414L10 8.586z" />
                </svg>
              </button>
            )}
          </div>
          {/* Search Results Count */}
          <div className="mt-3 text-sm text-muted-foreground text-center">
            {searchQuery && (
              <span>
                Found {filteredPosts.length} {filteredPosts.length === 1 ? 'post' : 'posts'}
              </span>
            )}
          </div>
        </div>

        {/* Compact Grid - 6 per row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 lg:gap-4">
          {filteredPosts.length > 0 ? (
            filteredPosts.map((post, index) => (
              <div
                key={index}
                className="w-full bg-card border border-border rounded-lg overflow-hidden shadow-lg hover:scale-105 hover:shadow-xl transition-all duration-300"
              >
                {/* Compact Instagram Header */}
                <div className="bg-secondary/10 px-2 py-1.5 flex items-center justify-between border-b border-border/50">
                  <div className="flex items-center gap-1.5">
                    {/* Brand Icon */}
                    <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-[8px]">V</span>
                    </div>
                    {/* Brand Info */}
                    <div className="min-w-0">
                      <div className="text-[9px] font-semibold text-foreground truncate">{post.brand}</div>
                      <div className="text-[7px] text-muted-foreground truncate">{post.tagline}</div>
                    </div>
                  </div>
                  {/* Menu Dots */}
                  <div className="text-foreground flex-shrink-0">
                    <svg width="10" height="10" viewBox="0 0 20 20" fill="currentColor">
                      <circle cx="10" cy="4" r="1.5" />
                      <circle cx="10" cy="10" r="1.5" />
                      <circle cx="10" cy="16" r="1.5" />
                    </svg>
                  </div>
                </div>

                {/* Compact Post Content */}
                <div className={`relative bg-gradient-to-br ${post.gradient} aspect-square flex flex-col items-center justify-center p-2`}>
                  {/* Geometric Background Pattern */}
                  <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-0 left-0 w-full h-full">
                      {[...Array(6)].map((_, i) => (
                        <div
                          key={i}
                          className="absolute border-white/20"
                          style={{
                            width: '200%',
                            height: '200%',
                            border: '1px solid',
                            transform: `rotate(${i * 30}deg)`,
                            left: '-50%',
                            top: '-50%'
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Compact Headline */}
                  <div className="relative z-10 text-center mb-1">
                    <h3 className="text-[11px] sm:text-xs font-black text-white leading-tight whitespace-pre-line">
                      {post.headline}
                    </h3>
                  </div>

                  {/* Compact Subtext */}
                  <div className="relative z-10 text-center">
                    <p className="text-[7px] sm:text-[8px] font-medium text-white/90 whitespace-pre-line">
                      {post.subtext}
                    </p>
                  </div>
                </div>

                {/* Compact Instagram Footer */}
                <div className="bg-secondary/10 px-2 py-1.5 flex items-center justify-between border-t border-border/50">
                  <div className="flex items-center gap-2">
                    {/* Heart */}
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                    </svg>
                    {/* Comment */}
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                    {/* Share */}
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground">
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                  </div>
                  {/* Bookmark */}
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-foreground">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                  </svg>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full text-center py-16">
              <p className="text-muted-foreground text-lg">No posts found matching "{searchQuery}"</p>
              <button
                onClick={() => setSearchQuery('')}
                className="mt-4 text-primary hover:text-primary/80 font-medium transition-colors"
              >
                Clear search
              </button>
            </div>
          )}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <p className="text-sm text-muted-foreground italic">
            Generate platform-ready content with AI-powered insights
          </p>
        </div>
      </div>
    </section>
  )
}

export default InstagramPostShowcase
