// Exam Categories Data
export interface ExamSubCategory {
  id: string;
  name: string;
}

export interface ExamCategory {
  id: string;
  name: string;
  fullName: string;
  color: string;
  bgColor: string;
  iconType: string;
  subcategories: ExamSubCategory[];
}

export const examCategories: ExamCategory[] = [
  {
    id: 'railway',
    name: 'Railway',
    fullName: 'Railway Recruitment Board',
    color: '#E53E3E',
    bgColor: '#FFF5F5',
    iconType: 'railway',
    subcategories: [
      { id: 'rrb-ntpc', name: 'RRB NTPC' },
      { id: 'rrb-group-d', name: 'RRB Group D' },
      { id: 'rrb-alp', name: 'RRB ALP' },
      { id: 'rrb-je', name: 'RRB JE' },
      { id: 'rrb-po', name: 'RRB PO' },
      { id: 'railway-loco-pilot', name: 'Loco Pilot' },
      { id: 'rrb-sse', name: 'RRB SSE' },
      { id: 'railway-technician', name: 'Technician' },
    ],
  },
  {
    id: 'upsc',
    name: 'UPSC',
    fullName: 'Union Public Service Commission',
    color: '#744210',
    bgColor: '#FFFBEB',
    iconType: 'upsc',
    subcategories: [
      { id: 'upsc-cse', name: 'UPSC CSE' },
      { id: 'upsc-capf', name: 'UPSC CAPF' },
      { id: 'upsc-ifs', name: 'UPSC IFS' },
      { id: 'upsc-ese', name: 'UPSC ESE' },
      { id: 'upsc-geo', name: 'UPSC Geo Scientist' },
      { id: 'upsc-nda', name: 'UPSC NDA' },
      { id: 'upsc-cds', name: 'UPSC CDS' },
    ],
  },
  {
    id: 'ssc',
    name: 'SSC',
    fullName: 'Staff Selection Commission',
    color: '#2B6CB0',
    bgColor: '#EBF8FF',
    iconType: 'ssc',
    subcategories: [
      { id: 'ssc-cgl', name: 'SSC CGL' },
      { id: 'ssc-chsl', name: 'SSC CHSL' },
      { id: 'ssc-mts', name: 'SSC MTS' },
      { id: 'ssc-gd', name: 'SSC GD Constable' },
      { id: 'ssc-cpo', name: 'SSC CPO' },
      { id: 'ssc-je', name: 'SSC JE' },
      { id: 'ssc-steno', name: 'SSC Stenographer' },
      { id: 'ssc-selection-post', name: 'SSC Selection Post' },
    ],
  },
  {
    id: 'banking',
    name: 'Banking',
    fullName: 'Banking & Insurance Exams',
    color: '#276749',
    bgColor: '#F0FFF4',
    iconType: 'banking',
    subcategories: [
      { id: 'ibps-po', name: 'IBPS PO' },
      { id: 'ibps-clerk', name: 'IBPS Clerk' },
      { id: 'sbi-po', name: 'SBI PO' },
      { id: 'sbi-clerk', name: 'SBI Clerk' },
      { id: 'rbi-grade-b', name: 'RBI Grade B' },
      { id: 'rbi-assistant', name: 'RBI Assistant' },
      { id: 'ibps-so', name: 'IBPS SO' },
      { id: 'lic-aao', name: 'LIC AAO' },
      { id: 'nabard', name: 'NABARD' },
    ],
  },
  {
    id: 'police',
    name: 'Police',
    fullName: 'Police & Paramilitary Exams',
    color: '#1A365D',
    bgColor: '#EBF8FF',
    iconType: 'police',
    subcategories: [
      { id: 'up-police', name: 'UP Police' },
      { id: 'delhi-police', name: 'Delhi Police' },
      { id: 'rajasthan-police', name: 'Rajasthan Police' },
      { id: 'bihar-police', name: 'Bihar Police' },
      { id: 'mp-police', name: 'MP Police' },
      { id: 'haryana-police', name: 'Haryana Police' },
      { id: 'cisf', name: 'CISF' },
      { id: 'crpf', name: 'CRPF' },
    ],
  },
  {
    id: 'tnpsc',
    name: 'TNPSC',
    fullName: 'Tamil Nadu Public Service Commission',
    color: '#B7791F',
    bgColor: '#FFFBEB',
    iconType: 'tnpsc',
    subcategories: [
      { id: 'tnpsc-group-1', name: 'TNPSC Group 1' },
      { id: 'tnpsc-group-2', name: 'TNPSC Group 2' },
      { id: 'tnpsc-group-4', name: 'TNPSC Group 4' },
      { id: 'tnpsc-vao', name: 'TNPSC VAO' },
      { id: 'tnpsc-group-7', name: 'TNPSC Group 7' },
    ],
  },
  {
    id: 'state',
    name: 'State Exams',
    fullName: 'State Government Exams',
    color: '#2C7A7B',
    bgColor: '#E6FFFA',
    iconType: 'state',
    subcategories: [
      { id: 'uppsc', name: 'UPPSC' },
      { id: 'bpsc', name: 'BPSC' },
      { id: 'mpsc', name: 'MPSC' },
      { id: 'rpsc', name: 'RPSC' },
      { id: 'appsc', name: 'APPSC' },
      { id: 'tspsc', name: 'TSPSC' },
      { id: 'wbpsc', name: 'WBPSC' },
      { id: 'kpsc', name: 'KPSC' },
    ],
  },
  {
    id: 'defence',
    name: 'Defence',
    fullName: 'Defence & Armed Forces Exams',
    color: '#2D3748',
    bgColor: '#EDF2F7',
    iconType: 'defence',
    subcategories: [
      { id: 'nda', name: 'NDA' },
      { id: 'cds', name: 'CDS' },
      { id: 'afcat', name: 'AFCAT' },
      { id: 'territorial-army', name: 'Territorial Army' },
      { id: 'agniveer', name: 'Agniveer' },
      { id: 'navy-mr', name: 'Navy MR' },
      { id: 'airforce-x-y', name: 'Airforce X/Y' },
    ],
  },
  {
    id: 'teaching',
    name: 'Teaching',
    fullName: 'Teaching & Education Exams',
    color: '#553C9A',
    bgColor: '#FAF5FF',
    iconType: 'teaching',
    subcategories: [
      { id: 'ctet', name: 'CTET' },
      { id: 'tet', name: 'State TET' },
      { id: 'dsssb', name: 'DSSSB' },
      { id: 'kv-pgt', name: 'KVS PGT' },
      { id: 'kv-tgt', name: 'KVS TGT' },
      { id: 'net', name: 'UGC NET' },
      { id: 'set', name: 'SET' },
    ],
  },
];

// PYQ Papers mock data
export interface PYQPaper {
  id: string;
  examId: string;
  subcategoryId: string;
  title: string;
  year: number;
  shift?: string;
  questions: number;
  duration: number; // minutes
  language: string[];
  hasOnlineView: boolean;
  hasPDF: boolean;
}

export const pyqPapers: PYQPaper[] = [
  { id: 'rrb-ntpc-2024-1', examId: 'railway', subcategoryId: 'rrb-ntpc', title: 'RRB NTPC CBT-1 2024', year: 2024, shift: 'Shift 1', questions: 100, duration: 90, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'rrb-ntpc-2024-2', examId: 'railway', subcategoryId: 'rrb-ntpc', title: 'RRB NTPC CBT-1 2024', year: 2024, shift: 'Shift 2', questions: 100, duration: 90, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'rrb-gd-2024', examId: 'railway', subcategoryId: 'rrb-group-d', title: 'RRB Group D 2024', year: 2024, questions: 100, duration: 90, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'rrb-ntpc-2022', examId: 'railway', subcategoryId: 'rrb-ntpc', title: 'RRB NTPC CBT-1 2022', year: 2022, questions: 100, duration: 90, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'rrb-alp-2024', examId: 'railway', subcategoryId: 'rrb-alp', title: 'RRB ALP 2024', year: 2024, questions: 75, duration: 60, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },

  { id: 'upsc-cse-2024', examId: 'upsc', subcategoryId: 'upsc-cse', title: 'UPSC CSE Prelims 2024', year: 2024, questions: 100, duration: 120, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'upsc-cse-2023', examId: 'upsc', subcategoryId: 'upsc-cse', title: 'UPSC CSE Prelims 2023', year: 2023, questions: 100, duration: 120, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'upsc-cse-2022', examId: 'upsc', subcategoryId: 'upsc-cse', title: 'UPSC CSE Prelims 2022', year: 2022, questions: 100, duration: 120, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'upsc-capf-2024', examId: 'upsc', subcategoryId: 'upsc-capf', title: 'UPSC CAPF AC 2024', year: 2024, questions: 125, duration: 120, language: ['English'], hasOnlineView: true, hasPDF: true },

  { id: 'ssc-cgl-2024-t1', examId: 'ssc', subcategoryId: 'ssc-cgl', title: 'SSC CGL Tier-1 2024', year: 2024, shift: 'Shift 1', questions: 100, duration: 60, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'ssc-chsl-2024', examId: 'ssc', subcategoryId: 'ssc-chsl', title: 'SSC CHSL Tier-1 2024', year: 2024, questions: 100, duration: 60, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'ssc-mts-2024', examId: 'ssc', subcategoryId: 'ssc-mts', title: 'SSC MTS 2024', year: 2024, questions: 90, duration: 90, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'ssc-gd-2024', examId: 'ssc', subcategoryId: 'ssc-gd', title: 'SSC GD Constable 2024', year: 2024, questions: 80, duration: 60, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },

  { id: 'ibps-po-2024', examId: 'banking', subcategoryId: 'ibps-po', title: 'IBPS PO Prelims 2024', year: 2024, questions: 100, duration: 60, language: ['English'], hasOnlineView: true, hasPDF: true },
  { id: 'sbi-po-2024', examId: 'banking', subcategoryId: 'sbi-po', title: 'SBI PO Prelims 2024', year: 2024, questions: 100, duration: 60, language: ['English'], hasOnlineView: true, hasPDF: true },
  { id: 'ibps-clerk-2024', examId: 'banking', subcategoryId: 'ibps-clerk', title: 'IBPS Clerk Prelims 2024', year: 2024, questions: 100, duration: 60, language: ['English'], hasOnlineView: true, hasPDF: true },
  { id: 'rbi-grade-b-2024', examId: 'banking', subcategoryId: 'rbi-grade-b', title: 'RBI Grade B 2024', year: 2024, questions: 200, duration: 120, language: ['English'], hasOnlineView: true, hasPDF: true },

  { id: 'up-police-2024', examId: 'police', subcategoryId: 'up-police', title: 'UP Police Constable 2024', year: 2024, questions: 150, duration: 120, language: ['Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'delhi-police-2024', examId: 'police', subcategoryId: 'delhi-police', title: 'Delhi Police HC 2024', year: 2024, questions: 100, duration: 90, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },

  { id: 'tnpsc-g1-2024', examId: 'tnpsc', subcategoryId: 'tnpsc-group-1', title: 'TNPSC Group 1 2024', year: 2024, questions: 200, duration: 180, language: ['Tamil', 'English'], hasOnlineView: true, hasPDF: true },
  { id: 'tnpsc-g2-2024', examId: 'tnpsc', subcategoryId: 'tnpsc-group-2', title: 'TNPSC Group 2A 2024', year: 2024, questions: 200, duration: 180, language: ['Tamil', 'English'], hasOnlineView: true, hasPDF: true },

  { id: 'nda-2024-1', examId: 'defence', subcategoryId: 'nda', title: 'NDA & NA (I) 2024', year: 2024, questions: 270, duration: 300, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'cds-2024-1', examId: 'defence', subcategoryId: 'cds', title: 'CDS (I) 2024', year: 2024, questions: 120, duration: 120, language: ['English'], hasOnlineView: true, hasPDF: true },

  { id: 'ctet-2024', examId: 'teaching', subcategoryId: 'ctet', title: 'CTET Dec 2024 Paper 1', year: 2024, questions: 150, duration: 150, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'ctet-2024-p2', examId: 'teaching', subcategoryId: 'ctet', title: 'CTET Dec 2024 Paper 2', year: 2024, questions: 150, duration: 150, language: ['English', 'Hindi'], hasOnlineView: true, hasPDF: true },

  { id: 'uppsc-2023', examId: 'state', subcategoryId: 'uppsc', title: 'UPPSC PCS Prelims 2023', year: 2023, questions: 150, duration: 120, language: ['Hindi'], hasOnlineView: true, hasPDF: true },
  { id: 'bpsc-70-2024', examId: 'state', subcategoryId: 'bpsc', title: 'BPSC 70th Combined 2024', year: 2024, questions: 150, duration: 120, language: ['Hindi', 'English'], hasOnlineView: true, hasPDF: true },
];

export const getExamById = (id: string) => examCategories.find(e => e.id === id);
export const getPapersByExam = (examId: string) => pyqPapers.filter(p => p.examId === examId);
export const getPapersBySubcategory = (subcategoryId: string) => pyqPapers.filter(p => p.subcategoryId === subcategoryId);
