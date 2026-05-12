#!/usr/bin/env python3
import sys
from pathlib import Path

from src.debate_extended.debate_config import create_debate_from_config

def main():
    create_debate_from_config("configs/basic/if_artificial_consciousness_emerges_ai_entities_should_be_granted_legal_personhood_pro.json")
    

if __name__ == "__main__":
    sys.exit(main())
