from pathlib import Path
from secrets import token_urlsafe
p=Path(__file__).resolve().parents[1]/".env"
if p.exists(): raise SystemExit(".env exists; refusing overwrite")
p.write_text("PLATFORM_DB_PASSWORD="+token_urlsafe(32)+"\n"+"PLATFORM_API_KEY="+token_urlsafe(40)+"\nPLATFORM_PORT=8765\n")
p.chmod(0o600)
print("Generated private .env (mode 0600). Never commit it.")
