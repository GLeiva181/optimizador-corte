from flask import Flask, render_template, request, redirect, url_for
import plotly.graph_objs as go
import plotly.offline as opy

app = Flask(__name__)

placa = {"ancho": 200, "alto": 200}
piezas = []  # {"ancho": int, "alto": int, "cantidad": int}
grosor_corte = 0  # margen de sierra

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

    # Generar posiciones considerando grosor de corte
    posiciones = []
    x, y = 0, 0
    fila_max_h = 0
    for pieza in piezas:
        for _ in range(pieza["cantidad"]):
            w, h = pieza["ancho"], pieza["alto"]
            if x + w > placa["ancho"]:
                x = 0
                y += fila_max_h + grosor_corte
                fila_max_h = 0
            if y + h > placa["alto"]:
                continue  # no entra
            posiciones.append((x, y, w, h))
            x += w + grosor_corte
            fila_max_h = max(fila_max_h, h)

    # Plotly
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=placa["ancho"], y1=placa["alto"],
                  line=dict(color="black", width=3))
    for i, (x, y, w, h) in enumerate(posiciones):
        fig.add_shape(type="rect", x0=x, y0=y, x1=x+w, y1=y+h,
                      line=dict(color="blue"), fillcolor="lightblue")
        fig.add_annotation(x=x+w/2, y=y+h/2, text=f"{i+1}", showarrow=False)

    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Optimización de Corte",
                      xaxis=dict(range=[0, placa["ancho"]]),
                      yaxis=dict(range=[0, placa["alto"]]))

    graph_html = opy.plot(fig, auto_open=False, output_type='div')

    return render_template("index.html", graph_html=graph_html, piezas=piezas,
                           placa=placa, grosor_corte=grosor_corte)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
