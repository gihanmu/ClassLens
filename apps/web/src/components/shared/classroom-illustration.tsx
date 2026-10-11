import * as React from "react";
import { cn } from "@/lib/utils";

export function ClassroomHeroIllustration({ className }: { className?: string }) {
  return (
    <div className={cn("relative flex items-center justify-center select-none", className)}>
      <svg
        viewBox="0 0 520 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto max-w-lg drop-shadow-md"
        aria-hidden="true"
      >
        {/* Soft Background Blob */}
        <path
          d="M450 200C450 310.457 360.457 390 250 390C139.543 390 60 310.457 60 200C60 89.543 149.543 30 260 30C370.457 30 450 89.543 450 200Z"
          fill="#FFCF78"
          fillOpacity="0.18"
        />
        <path
          d="M480 230C480 330 390 380 290 380C190 380 110 320 110 220C110 120 190 60 290 60C390 60 480 130 480 230Z"
          fill="#5145F5"
          fillOpacity="0.08"
        />

        {/* Floating Math Symbols */}
        <g opacity="0.85">
          {/* Plus sign */}
          <circle cx="85" cy="110" r="22" fill="#D8F4E8" />
          <path d="M85 98V122M73 110H97" stroke="#10B981" strokeWidth="4" strokeLinecap="round" />

          {/* Minus sign */}
          <circle cx="435" cy="95" r="20" fill="#FFEAE4" />
          <path d="M424 95H446" stroke="#F76543" strokeWidth="4" strokeLinecap="round" />

          {/* Division / Fraction */}
          <circle cx="440" cy="270" r="18" fill="#ECEAFE" />
          <circle cx="440" cy="262" r="2.5" fill="#5145F5" />
          <path d="M432 270H448" stroke="#5145F5" strokeWidth="3" strokeLinecap="round" />
          <circle cx="440" cy="278" r="2.5" fill="#5145F5" />

          {/* Multiplication */}
          <circle cx="90" cy="290" r="16" fill="#FEF3C7" />
          <path d="M82 282L98 298M98 282L82 298" stroke="#D97706" strokeWidth="3" strokeLinecap="round" />
        </g>

        {/* Stacked Books at Bottom */}
        <g id="books">
          {/* Bottom Book (Brand Purple) */}
          <rect x="140" y="320" width="240" height="26" rx="6" fill="#5145F5" />
          <rect x="145" y="325" width="230" height="4" fill="#6B60F7" />
          <rect x="135" y="323" width="12" height="20" rx="3" fill="#FFEAE4" />

          {/* Middle Book (Coral) */}
          <rect x="165" y="294" width="205" height="26" rx="6" fill="#F76543" />
          <rect x="170" y="299" width="195" height="4" fill="#FA856A" />
          <rect x="160" y="297" width="12" height="20" rx="3" fill="#D8F4E8" />

          {/* Top Book (Mint) */}
          <rect x="190" y="270" width="170" height="24" rx="6" fill="#10B981" />
          <rect x="195" y="274" width="160" height="4" fill="#34D399" />
          <rect x="185" y="273" width="10" height="18" rx="3" fill="#FFCF78" />
        </g>

        {/* Friendly Classroom Character */}
        <g id="character">
          {/* Body / Sweater */}
          <path
            d="M200 270C200 210 220 185 260 185C300 185 320 210 320 270H200Z"
            fill="#5145F5"
          />
          {/* Collar */}
          <path d="M245 185L260 205L275 185H245Z" fill="#FFFFFF" />

          {/* Neck */}
          <rect x="250" y="165" width="20" height="22" rx="4" fill="#FBD5B5" />

          {/* Head */}
          <circle cx="260" cy="140" r="34" fill="#FBD5B5" />

          {/* Hair */}
          <path
            d="M226 135C226 112 241 95 260 95C279 95 294 112 294 135C294 139 293 143 291 146C289 125 277 115 260 115C243 115 231 125 229 146C227 143 226 139 226 135Z"
            fill="#3B261A"
          />
          {/* Hair Bun / Curls */}
          <circle cx="260" cy="90" r="14" fill="#3B261A" />

          {/* Round Teacher Glasses */}
          <circle cx="249" cy="138" r="9" stroke="#10182B" strokeWidth="2.5" fill="#FFFFFF" fillOpacity="0.4" />
          <circle cx="271" cy="138" r="9" stroke="#10182B" strokeWidth="2.5" fill="#FFFFFF" fillOpacity="0.4" />
          <path d="M258 138H262" stroke="#10182B" strokeWidth="2.5" />

          {/* Eyes behind glasses */}
          <circle cx="249" cy="138" r="2.5" fill="#10182B" />
          <circle cx="271" cy="138" r="2.5" fill="#10182B" />

          {/* Friendly Smile */}
          <path
            d="M253 154C256 158 264 158 267 154"
            stroke="#10182B"
            strokeWidth="2"
            strokeLinecap="round"
          />

          {/* Left Hand Holding Diagnostic Worksheet */}
          <g id="worksheet">
            <rect
              x="300"
              y="160"
              width="75"
              height="95"
              rx="6"
              fill="#FFFFFF"
              stroke="#E2E8F0"
              strokeWidth="2"
              transform="rotate(12 300 160)"
              filter="drop-shadow(0 4px 6px rgba(0,0,0,0.08))"
            />
            {/* Number line illustration on worksheet */}
            <path
              d="M312 195L365 206"
              stroke="#5145F5"
              strokeWidth="2"
              strokeLinecap="round"
            />
            {/* Hop arcs on worksheet */}
            <path
              d="M316 195Q326 182 336 199"
              stroke="#F76543"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
            <path
              d="M336 199Q348 185 360 204"
              stroke="#10B981"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          </g>
        </g>

        {/* Curved Floating Hop Arrow (Symbol of ClassLens Number Line Engine) */}
        <path
          d="M120 180 C 170 120, 230 120, 290 145"
          stroke="#5145F5"
          strokeWidth="3.5"
          strokeDasharray="6 6"
          fill="none"
          strokeLinecap="round"
        />
        <circle cx="120" cy="180" r="5" fill="#5145F5" />
        <path d="M285 137L295 146L282 150Z" fill="#5145F5" />
      </svg>
    </div>
  );
}
