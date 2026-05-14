"""Test data populator — NOT for production. Remove this file before shipping."""
import random

_FIRST = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Susan", "Richard", "Jessica",
    "Joseph", "Sarah", "Thomas", "Karen", "Charles", "Lisa", "Christopher",
    "Nancy", "Daniel", "Betty", "Matthew", "Margaret", "Anthony", "Sandra",
    "Mark", "Ashley", "Donald", "Dorothy", "Steven", "Kimberly", "Paul",
]

_LAST = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
]

_KEYWORDS = [
    "retired", "teacher", "nurse", "engineer", "veteran", "lawyer",
    "accountant", "manager", "self-employed", "doctor", "construction",
    "trucker", "pastor", "homemaker", "student", "police", "firefighter",
    "banker", "scientist", "artist", "social worker", "IT", "sales",
]

_NOTES = [
    "Seemed attentive during voir dire.",
    "Has prior jury experience.",
    "Expressed strong opinions on law enforcement.",
    "Asked several clarifying questions.",
    "Appeared distracted at times.",
    "Very engaged, took notes.",
    "Mentioned personal experience with the court system.",
    "Has a family member in law enforcement.",
    "Nodded frequently during prosecution's opening.",
    "Stated belief in presumption of innocence.",
    "Works long hours, concerned about schedule.",
    "Has strong feelings about the subject matter.",
    "Quiet, difficult to read.",
    "Very forthcoming in responses.",
    "Mentioned watching a lot of true crime content.",
    "",
    "",
]


def populate(app):
    """Fill every seat with a randomly generated juror."""
    import sys
    Juror = sys.modules.get("jury", sys.modules["__main__"]).Juror

    # Clear existing data
    app.jurors.clear()
    app.final_jury.clear()
    Juror._next = 1

    try:
        rows = max(1, int(app.rows_var.get()))
        cols = max(1, int(app.cols_var.get()))
    except Exception:
        rows, cols = 4, 7

    total = rows * cols
    app.seats = {i: None for i in range(1, total + 1)}

    used_names = set()
    for sn in range(1, total + 1):
        # Generate a unique name
        for _ in range(100):
            name = f"{random.choice(_FIRST)} {random.choice(_LAST)}"
            if name not in used_names:
                used_names.add(name)
                break

        age      = str(random.randint(22, 72))
        kw_count = random.randint(0, 3)
        keywords = ", ".join(random.sample(_KEYWORDS, kw_count)) if kw_count else ""
        notes    = random.choice(_NOTES)

        j = Juror(name, age, notes, keywords)
        j.seat   = sn
        j.status = "seated"
        app.jurors[j.id] = j
        app.seats[sn]    = j.id

    app._refresh()
