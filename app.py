from flask import Flask, render_template, request, redirect, url_for, send_file
import plotly.graph_objs as go
import plotly.offline as opy
import csv
import io

app = Flask(__name__)

placa = {"ancho": 200, "alto": 200}
piezas = []  # {"ancho": int, "alto": int, "cantidad": int}
grosor_corte = 0  # pérdida de material por sierra


def distribuir_piezas(piezas, placa_ancho, placa_alto, grosor):
    posiciones = []
    piezas_no_cabidas = []

    for idx, pieza in enumerate(piezas):
        for _ in range(pieza["cantidad"]):
            w, h = pieza["ancho"], pieza["alto"]
            colocada = False
            y = 0
            while y + h <= placa_alto:
                x = 0
                while x + w <= placa_ancho:
                    collision = False
                    for px, py, pw, ph in posiciones:
                        if not (x + w + grosor <= px or x >= px + pw + grosor or
                                y + h + grosor <= py or y >= py + ph + grosor):
                            collision = True
                            break
                    if not collision:
                        posiciones.append((x, y, w, h))
                        colocada = True
                        break
                    x += 1
                if colocada:
                    break
                y += 1
            if not colocada:
                piezas_no_cabidas.append((pieza, idx))
    return posiciones, piezas_no_cabidas


@app.route("/", methods=["GET", "POST"])
def index():
    global placa, piezas, grosor_corte

    if request.method == "POST":
        if "placa" in request.form:
            placa["ancho"] = int(request.form["ancho"])
            placa["alto"] = int(request.form["alto"])
            grosor_corte = int(request.form.get("grosor_corte", 0))
        elif "pieza" in request.form:
            ancho = int(request.form["p_ancho"])
            alto = int(request.form["p_alto"])
            cantidad = int(request.form["p_cantidad"])
            piezas.append({"ancho": ancho, "alto": alto, "cantidad": cantidad})
        elif "reset" in request.form:
            piezas.clear()
        elif "importar" in request.form and "file" in request.files:
            file = request.files["file"]
            if file.filename.endswith(".csv"):
                piezas.clear()
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                reader = csv.DictReader(stream)
                for row in reader:
                    piezas.append({
                        "ancho": int(row["ancho"]),
                        "alto": int(row["alto"]),
                        "cantidad": int(row["cantidad"])
                    })

    posiciones, piezas_no_cabidas = distribuir_piezas(piezas, placa["ancho"], placa["alto"], grosor_corte)

    # Plotly
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=placa["ancho"], y1=placa["alto"],
                  line=dict(color="black", width=3))
    for i, (x, y, w, h) in enumerate(posiciones):
        fig.add_shape(type="rect", x0=x, y0=y, x1=x+w, y1=y+h,
                      line=dict(color="blue"), fillcolor="lightblue")
        fig.add_annotation(x=x + w / 2, y=y + h / 2, text=f"{i+1}", showarrow=False)

    # piezas que no entran
    for pieza, idx in piezas_no_cabidas:
        fig.add_shape(type="rect", x0=0, y0=0, x1=pieza["ancho"], y1=pieza["alto"],
                      line=dict(color="red", width=2), fillcolor="red", opacity=0.3)

    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Optimización de Corte",
                      xaxis=dict(range=[0, placa["ancho"]]),
                      yaxis=dict(range=[0, placa["alto"]]))
    graph_html = opy.plot(fig, auto_open=False, output_type='div')

    return render_template("index.html", graph_html=graph_html, piezas=piezas,
                           placa=placa, grosor_corte=grosor_corte,
                           piezas_no_cabidas=piezas_no_cabidas)


@app.route("/delete/<int:index>")
def delete(index):
    if 0 <= index < len(piezas):
        piezas.pop(index)
    return redirect(url_for("index"))


@app.route("/rotate/<int:index>")
def rotate(index):
    if 0 <= index < len(piezas):
        pieza = piezas[index]
        pieza["ancho"], pieza["alto"] = pieza["alto"], pieza["ancho"]
    return redirect(url_for("index"))


@app.route("/update/<int:index>", methods=["POST"])
def update(index):
    if 0 <= index < len(piezas):
        piezas[index]["ancho"] = int(request.form.get("ancho", piezas[index]["ancho"]))
        piezas[index]["alto"] = int(request.form.get("alto", piezas[index]["alto"]))
        piezas[index]["cantidad"] = int(request.form.get("cantidad", piezas[index]["cantidad"]))
    return redirect(url_for("index"))


@app.route("/exportar")
def exportar():
    global piezas
    siO = io.StringIO()
    writer = csv.DictWriter(siO, fieldnames=["ancho", "alto", "cantidad"])
    writer.writeheader()
    for pieza in piezas:
        writer.writerow(pieza)
    siO.seek(0)
    return send_file(io.BytesIO(siO.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     download_name="piezas.csv",
                     as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
