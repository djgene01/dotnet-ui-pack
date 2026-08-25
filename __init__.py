from pathlib import Path


def register(ctx):
    skills_dir = Path(__file__).resolve().parent / "skills"
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            ctx.register_skill(skill_md.parent.name, skill_md)
        except Exception:
            pass  # one bad skill must not break siblings
