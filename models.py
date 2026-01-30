import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional

              
# Represents a single assessment item with a weight and optional mark
@dataclass
class Assessment:
    name: str
    kind: str
    weight: float
    mark: Optional[float] = None

# Represents a subject containing a list of assessments
@dataclass
class Subject:
    title: str
    assessments: List[Assessment] = field(default_factory=list)

              
# Manages the collection of subjects and their data
class GradeBook:
    # Initializes an empty gradebook
    def __init__(self):
        self.subjects: Dict[str, Subject] = {}

                 
    # Adds a new subject by title
    def add_subject(self, title: str):
        if title in self.subjects:
            raise ValueError("Subject already exists.")
        self.subjects[title] = Subject(title=title)

                    
    # Removes a subject by title
    def remove_subject(self, title: str):
        if title in self.subjects:
            del self.subjects[title]

                    
    # Renames an existing subject
    def rename_subject(self, old: str, new: str):
        if old not in self.subjects:
            raise ValueError("Subject not found.")
        if new in self.subjects and new != old:
            raise ValueError("Another subject with that name already exists.")
        subj = self.subjects.pop(old)
        subj.title = new
        self.subjects[new] = subj

                    
    # Adds an assessment to a specific subject
    def add_assessment(self, subj: str, a: Assessment):
        if subj not in self.subjects:
            raise ValueError("Subject not found.")
        self.subjects[subj].assessments.append(a)

                       
    # Removes an assessment from a subject by index
    def delete_assessment(self, subj: str, index: int):
        self.subjects[subj].assessments.pop(index)

               
    # Serializes the gradebook data to a JSON string
    def as_json(self) -> str:
        raw = {k: {"title": v.title, "assessments": [asdict(a) for a in v.assessments]}
               for k, v in self.subjects.items()}
        return json.dumps(raw, indent=2)

                 
    # Loads gradebook data from a JSON string
    def load_json(self, s: str):
        data = json.loads(s)
        self.subjects.clear()
        for k, v in data.items():
            subj = Subject(title=v["title"])
            for a in v.get("assessments", []):
                subj.assessments.append(Assessment(
                    name=a["name"],
                    kind=a.get("kind", "Assessment"),
                    weight=float(a["weight"]),
                    mark=(None if a.get("mark") is None else float(a["mark"])),
                ))
            self.subjects[subj.title] = subj
