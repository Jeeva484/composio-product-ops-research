from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ResearchFinding(BaseModel):
    rank: int
    app: str
    category: str
    description: str
    what_it_does: str
    auth_methods: str = "Unknown"
    public_rest_api: str = "Unknown"
    graphql_api: str = "Unknown"
    api_breadth: str = "Unknown"
    access: str = "Requires Verification"
    official_mcp: str = "Unknown"
    community_mcp: str = "Unknown"
    buildability: str = "Requires Research"
    main_blocker: str = "Official documentation and account terms require verification"
    evidence_url: Optional[HttpUrl] = None
    evidence: str = "Official documentation URL recorded; classification not yet verified"
    confidence: Confidence = Confidence.LOW
    last_researched: str

    @property
    def csv_dict(self):
        return {
            "rank": self.rank,
            "app": self.app,
            "category": self.category,
            "description": self.description,
            "what_it_does": self.what_it_does,
            "auth_methods": self.auth_methods,
            "access": self.access,
            "public_rest_api": self.public_rest_api,
            "graphql_api": self.graphql_api,
            "api_breadth": self.api_breadth,
            "official_mcp": self.official_mcp,
            "community_mcp": self.community_mcp,
            "buildability": self.buildability,
            "main_blocker": self.main_blocker,
            "evidence_url": str(self.evidence_url) if self.evidence_url else "",
            "evidence": self.evidence,
            "confidence": self.confidence.value,
            "last_researched": self.last_researched,
        }
