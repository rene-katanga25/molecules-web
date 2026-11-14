from __future__ import annotations
import math
import streamlit as st

st.set_page_config(page_title="Molécules - Température d'ébullition", page_icon="🧪", layout="centered")

# --- CSS Personnalisé ---
st.markdown("""
<style>
  .temp {
    background: #f97316; color: #fff;
    padding: 14px 28px; border-radius: 14px;
    text-align: center; margin-bottom: 20px;
  }
  .temp .label { font-size: 14px; opacity: 0.9; }
  .temp .value { font-size: 34px; font-weight: bold; }
  .temp .kelvin { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

st.title("🧪 Molécules - Température d'ébullition")

# Formulaire de recherche
with st.form(key="search_form"):
    compound = st.text_input("Nom du composé (ex : ethanol, acetic acid, H2SO4)", value="")
    submit_button = st.form_submit_button(label="Chercher")

def get_boiling_point_celsius(compound_name: str):
    try:
        from thermo import Chemical
        chemical = Chemical(compound_name)
    except Exception as exc:
        return None, f"Composé introuvable ou non reconnu : {compound_name!r}."

    try:
        kelvin = float(chemical.Tb)
    except (TypeError, ValueError):
        return None, f"Aucune température d'ébullition pour {compound_name!r}."
    if not math.isfinite(kelvin):
        return None, f"Température inexploitable pour {compound_name!r}."
    return kelvin - 273.15, None

if compound:
    temperature, erreur = get_boiling_point_celsius(compound.strip())
    
    if erreur:
        st.error(erreur)
    elif temperature is not None:
        st.subheader(compound.capitalize())
        
        # Affichage de la température
        st.markdown(f"""
        <div class="temp">
          <div class="label">Température d'ébullition normale (1 atm)</div>
          <div class="value">{temperature:.2f} °C</div>
          <div class="kelvin">{temperature + 273.15:.2f} K</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Visualisation 2D / 3D via PubChem & 3Dmol dans Streamlit
        st.markdown("### Visualisation de la molécule")
        
        pubchem_base = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound.strip()}"
        
        viewer_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.4/3Dmol-min.js"></script>
          <style>
            .panel { width: 100%; max-width: 560px; height: 420px; border-radius: 14px; background: #1e293b; position: relative; overflow: hidden; margin: auto; }
            #viewer { width: 100%; height: 100%; position: relative; }
            #view2d { display: none; width: 100%; height: 100%; align-items: center; justify-content: center; background: #ffffff; }
            #view2d img { max-width: 100%; max-height: 100%; }
            .buttons { display: flex; gap: 10px; margin-bottom: 12px; justify-content: center; }
            button { padding: 8px 20px; font-size: 14px; cursor: pointer; border: 2px solid #38bdf8; background: transparent; color: #38bdf8; border-radius: 8px; }
            button.active { background: #38bdf8; color: #0f172a; font-weight: bold; }
            #message { margin-top: 8px; color: #fbbf24; text-align: center; font-size: 13px; }
          </style>
        </head>
        <body>
          <div class="buttons">
            <button id="btn3d" class="active" onclick="montrer('3d')">3D</button>
            <button id="btn2d" onclick="montrer('2d')">2D</button>
          </div>
          <div class="panel">
            <div id="viewer"></div>
            <div id="view2d"><img id="img2d" alt="Structure 2D" src="__PUBCHEM_BASE__/PNG?image_size=500x400"></div>
          </div>
          <div id="message">Chargement de la molécule...</div>

          <script>
            const base = "__PUBCHEM_BASE__";
            const message = document.getElementById("message");
            const viewerDiv = document.getElementById("viewer");
            const view2d = document.getElementById("view2d");
            const btn3d = document.getElementById("btn3d");
            const btn2d = document.getElementById("btn2d");

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
                  message.textContent = "Pas de modèle 3D disponible : structure plane affichée.";
                } catch (e2) {
                  message.textContent = "Molécule introuvable sur PubChem.";
                  return;
                }
              }
              viewer.addModel(sdf, "sdf");
              viewer.setStyle({}, { stick: { radius: 0.15 }, sphere: { scale: 0.28 } });
              viewer.zoomTo();
              viewer.render();

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

            afficher3D();
          </script>
        </body>
        </html>
        """
        
        # Injection propre de l'URL PubChem sans conflit d'accolades
        viewer_html = viewer_html.replace("__PUBCHEM_BASE__", pubchem_base)
        
        st.components.v1.html(viewer_html, height=520)