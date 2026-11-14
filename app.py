"""Site web : temperature d'ebullition + molecule 2D/3D rotative."""

from __future__ import annotations

import html
import json
import math

from flask import Flask, request

app = Flask(__name__)

LT = "\x3c"  # le signe "plus petit que", ecrit de facon protegee


def get_boiling_point_celsius(compound: str):
    """Retourne (temperature_C, message_erreur)."""
    try:
        from thermo import Chemical
        chemical = Chemical(compound)
    except Exception as exc:
        print("ERREUR REELLE :", repr(exc))
        return None, f"Compose introuvable ou non reconnu : {compound!r}."

    try:
        kelvin = float(chemical.Tb)
    except (TypeError, ValueError):
        return None, f"Aucune temperature d'ebullition pour {compound!r}."
    if not math.isfinite(kelvin):
        return None, f"Temperature inexploitable pour {compound!r}."
    return kelvin - 273.15, None


PAGE = """\x3c!DOCTYPE html>
\x3chtml lang="fr">
\x3chead>
\x3cmeta charset="UTF-8">
\x3cmeta name="viewport" content="width=device-width, initial-scale=1">
\x3ctitle>Molecules - temperature d'ebullition\x3c/title>
\x3cscript src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.4/3Dmol-min.js">\x3c/script>
\x3cstyle>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px;
    font-family: Segoe UI, Arial, sans-serif;
    background: #0f172a; color: #e2e8f0;
    display: flex; flex-direction: column; align-items: center;
  }
  h1 { margin: 0 0 16px; text-transform: capitalize; }
  form { margin-bottom: 20px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
  input[type=text] {
    padding: 10px 14px; font-size: 16px; border-radius: 10px;
    border: 2px solid #38bdf8; background: #1e293b; color: #e2e8f0;
    width: 260px;
  }
  button {
    padding: 10px 26px; font-size: 16px; cursor: pointer;
    border: 2px solid #38bdf8; background: transparent;
    color: #38bdf8; border-radius: 10px;
  }
  button.active { background: #38bdf8; color: #0f172a; font-weight: bold; }
  .temp {
    background: #f97316; color: #fff;
    padding: 14px 28px; border-radius: 14px;
    text-align: center; margin-bottom: 20px;
  }
  .temp .label { font-size: 14px; opacity: 0.9; }
  .temp .value { font-size: 34px; font-weight: bold; }
  .temp .kelvin { font-size: 16px; }
  .erreur { color: #fbbf24; margin-bottom: 20px; text-align: center; }
  .buttons { display: flex; gap: 10px; margin-bottom: 16px; }
  .panel {
    width: 100%; max-width: 560px; height: 420px;
    border-radius: 14px; background: #1e293b; position: relative;
    overflow: hidden;
  }
  #viewer { width: 100%; height: 100%; position: relative; }
  #view2d {
    display: none; width: 100%; height: 100%;
    align-items: center; justify-content: center; background: #ffffff;
  }
  #view2d img { max-width: 100%; max-height: 100%; }
  #message { margin-top: 12px; color: #fbbf24; min-height: 20px; text-align: center; }
  .hint { margin-top: 6px; font-size: 13px; color: #94a3b8; }
\x3c/style>
\x3c/head>
\x3cbody>
  \x3cform method="get" action="/">
    \x3cinput type="text" name="compose" value="__COMPOSE__"
           placeholder="ex : ethanol, acetic acid, H2SO4" autofocus>
    \x3cbutton type="submit" class="active">Chercher\x3c/button>
  \x3c/form>
  __RESULTAT__
  __SCRIPT__
\x3c/body>
\x3c/html>
"""

SCRIPT_MOLECULE = """
  const base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" +
               encodeURIComponent(NOM);
  const message = document.getElementById("message");
  const viewerDiv = document.getElementById("viewer");
  const view2d = document.getElementById("view2d");
  const btn3d = document.getElementById("btn3d");
  const btn2d = document.getElementById("btn2d");

  document.getElementById("img2d").src = base + "/PNG?image_size=500x400";

  const viewer = $3Dmol.createViewer("viewer", { backgroundColor: "#1e293b" });

  async function charger(typeRecord) {
    const rep = await fetch(base + "/SDF?record_type=" + typeRecord);
    if (!rep.ok) throw new Error("HTTP " + rep.status);
    return rep.text();
  }

  async function afficher3D() {
    let sdf;
    try {
      sdf = await charger("3d");
    } catch (e) {
      try {
        sdf = await charger("2d");
        message.textContent = "Pas de modele 3D disponible : structure plane affichee.";
      } catch (e2) {
        message.textContent = "Molecule introuvable sur PubChem (essayez le nom anglais).";
        return;
      }
    }
    viewer.addModel(sdf, "sdf");
    viewer.setStyle({}, { stick: { radius: 0.15 }, sphere: { scale: 0.28 } });
    viewer.zoomTo();
    viewer.render();

    // Un tour complet autour de Y, puis X, puis Z, et on recommence.
    const axes = ["y", "x", "z"];
    let i = 0, angle = 0;
    setInterval(() => {
      viewer.rotate(1, axes[i]);
      viewer.render();
      angle += 1;
      if (angle >= 360) { angle = 0; i = (i + 1) % 3; }
    }, 20);

    if (message.textContent.startsWith("Chargement")) message.textContent = "";
  }

  function montrer(mode) {
    const is3d = mode === "3d";
    viewerDiv.style.display = is3d ? "block" : "none";
    view2d.style.display = is3d ? "none" : "flex";
    btn3d.classList.toggle("active", is3d);
    btn2d.classList.toggle("active", !is3d);
    if (is3d) { viewer.resize(); viewer.render(); }
  }

  btn3d.addEventListener("click", () => montrer("3d"));
  btn2d.addEventListener("click", () => montrer("2d"));

  afficher3D();
"""


def construire_page(compound: str = "", temperature=None, erreur=None) -> str:
    resultat = ""
    script = ""

    if erreur:
        resultat = f'{LT}div class="erreur">' + html.escape(erreur) + f"{LT}/div>"
    elif temperature is not None:
        resultat = (
            f"{LT}h1>" + html.escape(compound) + f"{LT}/h1>"
            f'{LT}div class="temp">'
            f'{LT}div class="label">Temperature d\'ebullition normale (1 atm){LT}/div>'
            f'{LT}div class="value">{temperature:.2f} &deg;C{LT}/div>'
            f'{LT}div class="kelvin">{temperature + 273.15:.2f} K{LT}/div>'
            f"{LT}/div>"
            f'{LT}div class="buttons">'
            f'{LT}button id="btn3d" class="active">3D{LT}/button>'
            f'{LT}button id="btn2d">2D{LT}/button>'
            f"{LT}/div>"
            f'{LT}div class="panel">'
            f'{LT}div id="viewer">{LT}/div>'
            f'{LT}div id="view2d">{LT}img id="img2d" alt="Structure 2D">{LT}/div>'
            f"{LT}/div>"
            f'{LT}div id="message">Chargement de la molecule...{LT}/div>'
            f'{LT}div class="hint">3D : clic gauche = tourner, molette = zoom{LT}/div>'
        )
        nom_json = json.dumps(compound).replace(LT, "\\u003c")
        script = f"{LT}script>const NOM = " + nom_json + ";" + SCRIPT_MOLECULE + f"{LT}/script>"

    return (
        PAGE
        .replace("__COMPOSE__", html.escape(compound, quote=True))
        .replace("__RESULTAT__", resultat)
        .replace("__SCRIPT__", script)
    )


@app.route("/")
def accueil():
    compound = request.args.get("compose", "").strip()
    if not compound:
        return construire_page()
    temperature, erreur = get_boiling_point_celsius(compound)
    return construire_page(compound, temperature, erreur)


if __name__ == "__main__":
    app.run(debug=True)