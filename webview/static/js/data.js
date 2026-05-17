/* Sample data — mirrors Example.png from the source repo */

window.JURORS = [
  { id: 1,  name: "James Smith",         age: 48, status: "excused",     seat: 1,  panel: 1 },
  { id: 2,  name: "Mary Johnson",        age: 60, status: "struck_def",  seat: 2,  panel: 1, rating: 1 },
  { id: 3,  name: "Robert Williams",     age: 43, status: "seated",      seat: 3,  panel: 1 },
  { id: 4,  name: "Patricia Brown",      age: 35, status: "seated",      seat: 4,  panel: 1 },
  { id: 5,  name: "Michael Jones",       age: 71, status: "excused",     seat: 5,  panel: 1 },
  { id: 6,  name: "Linda Garcia",        age: 52, status: "seated",      seat: 6,  panel: 1 },
  { id: 7,  name: "William Miller",      age: 37, status: "final",       seat: 7,  panel: 1, finalNo: 2, rating: 3, keywords: "fireman", notes: "fell asleep during interview" },
  { id: 8,  name: "Barbara Davis",       age: 65, status: "seated",      seat: 8,  panel: 1 },
  { id: 10, name: "Susan Martinez",      age: 56, status: "seated",      seat: 10, panel: 1 },
  { id: 11, name: "Richard Hernandez",   age: 43, status: "struck_pro",  seat: 11, panel: 1, rating: -3 },
  { id: 12, name: "Jessica Lopez",       age: 27, status: "seated",      seat: 12, panel: 1 },
  { id: 13, name: "Joseph Gonzalez",     age: 76, status: "seated",      seat: 13, panel: 1 },
  { id: 14, name: "Sarah Wilson",        age: 39, status: "seated",      seat: 14, panel: 1 },
  { id: 15, name: "Thomas Anderson",     age: 59, status: "seated",      seat: 15, panel: 1 },
  { id: 16, name: "Karen Taylor",        age: 50, status: "seated",      seat: 16, panel: 1 },
  { id: 17, name: "Charles Thomas",      age: 45, status: "final",       seat: 17, panel: 1, finalNo: 1, rating: 2 },
  { id: 18, name: "Nancy Jackson",       age: 67, status: "seated",      seat: 18, panel: 1 },
  { id: 19, name: "Christopher White",   age: 33, status: "seated",      seat: 19, panel: 1, keywords: "trucker" },
  { id: 20, name: "Betty Harris",        age: 62, status: "struck_def",  seat: 20, panel: 1 },
  { id: 21, name: "Daniel Martin",       age: 38, status: "seated",      seat: 21, panel: 1 },
  { id: 22, name: "Margaret Thompson",   age: 55, status: "seated",      seat: 22, panel: 1 },
  { id: 24, name: "Sandra Martinez",     age: 60, status: "seated",      seat: 24, panel: 1 },
  { id: 25, name: "Mark Robinson",       age: 34, status: "seated",      seat: 25, panel: 1 },
  { id: 26, name: "Dorothy Lewis",       age: 71, status: "seated",      seat: 26, panel: 1 },
  { id: 27, name: "Steven Walker",       age: 42, status: "seated",      seat: 27, panel: 1 },
  { id: 28, name: "Kimberly Hall",       age: 29, status: "seated",      seat: 28, panel: 1 },

  /* Preliminary (un-seated) pool */
  { id: 9,  name: "David Rodriguez",     age: 41, status: "pool" },
  { id: 23, name: "Anthony Garcia",      age: 38, status: "pool" },

  /* One example of a "both struck" juror for the new bottom-left box */
  { id: 29, name: "Patricia Allen",      age: 58, status: "struck_both" },
];

window.SEAT_GRID = { rows: 4, cols: 7, jurySize: 12 };
window.SELECTED_SEAT_ID = 19; // Christopher White, per Example.png
