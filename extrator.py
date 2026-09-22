import re
import xml.etree.ElementTree as ET

NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def parse_numero_livre(texto):
    if texto is None:
        return None
    texto = texto.strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(".", "")
    try:
        return float(texto)
    except ValueError:
        return None


PADROES = {
    "placa": [
        r"Placa:\s*([A-Z0-9\-]+)",
        r"PLACA[:\s]+([A-Z0-9\-]+)",
        r"Veic(?:ulo)?[.:]?\s*([A-Z]{3}[\-\s]?\d[A-Z0-9]{3})",
    ],
    "motorista": [
        r"Motorista:\s*([A-ZÀ-Ú]+(?:\s[A-ZÀ-Ú]+){0,3})",
        r"MOT\s*[/.]?\s*OBS\s*:\s*([A-ZÀ-Ú]+(?:\s[A-ZÀ-Ú]+){0,3})",
        r"Cond(?:utor)?[.:]?\s*([A-ZÀ-Ú]+(?:\s[A-ZÀ-Ú]+){0,3})",
    ],
    "km_anterior": [
        r"KM\s*/?\s*HM\s*Ant\.?:\s*([\d.,]+)",
        r"KM\s*ANTERIOR[:\s]+([\d.,]+)",
    ],
    "km_atual": [
        r"KM\s*/?\s*HM:\s*([\d.,]+)",
        r"\bKM:\s*([\d.,]+)",
        r"KM\s*ATUAL[:\s]+([\d.,]+)",
    ],
    "media": [
        r"M[eé]dia:\s*([\d.,]+)",
        r"MEDIA[:\s]+([\d.,]+)",
    ],
    "tipo_veiculo": [
        r"Veiculo:\s*([A-ZÀ-Ú]+)\s*-",
        r"TIPO\s*VEICULO[:\s]+([A-ZÀ-Ú]+)",
    ],
}


def extrair_campo(campo, texto):
    for padrao in PADROES[campo]:
        m = re.search(padrao, texto, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extrair_dados_nfe(caminho_xml):
    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    tag_raiz = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag_raiz not in ("nfeProc", "NFe"):
        raise ValueError(
            f"Arquivo nao e uma NFe de produto (raiz: {tag_raiz}) - ignorado."
        )

    ide = root.find(".//nfe:ide", NS)
    emit = root.find(".//nfe:emit", NS)
    dest = root.find(".//nfe:dest", NS)
    produtos = root.findall(".//nfe:det/nfe:prod", NS)
    infCpl_el = root.find(".//nfe:infAdic/nfe:infCpl", NS)
    vNF_el = root.find(".//nfe:total/nfe:ICMSTot/nfe:vNF", NS)
    nfref_el = root.find(".//nfe:ide/nfe:NFref/nfe:refNFe", NS)
    eh_resumo_duplicado = nfref_el is not None and nfref_el.text

    infCpl = infCpl_el.text if infCpl_el is not None and infCpl_el.text else ""

    litros_total = 0.0
    nomes_produtos = []
    for p in produtos:
        qcom_el = p.find("nfe:qCom", NS)
        xprod_el = p.find("nfe:xProd", NS)
        ucom_el = p.find("nfe:uCom", NS)
        eh_litro = ucom_el is not None and ucom_el.text and ucom_el.text.strip().upper() == "L"
        if eh_litro and qcom_el is not None and qcom_el.text:
            litros_total += float(qcom_el.text)
        if eh_litro and xprod_el is not None and xprod_el.text:
            nomes_produtos.append(xprod_el.text)
    combustivel_nome = " + ".join(dict.fromkeys(nomes_produtos)) if nomes_produtos else None

    if vNF_el is not None and vNF_el.text:
        valor_pago = float(vNF_el.text)
    else:
        valor_pago = sum(
            float(p.find("nfe:vProd", NS).text)
            for p in produtos
            if p.find("nfe:vProd", NS) is not None and p.find("nfe:vProd", NS).text
        ) or None

    km_ant_txt = extrair_campo("km_anterior", infCpl)
    km_atual_txt = extrair_campo("km_atual", infCpl)
    media_txt = extrair_campo("media", infCpl)

    km_anterior = parse_numero_livre(km_ant_txt)
    km_atual = parse_numero_livre(km_atual_txt)
    media = parse_numero_livre(media_txt)

    def km_invalido(v):
        return v is not None and (v >= 9999990 or v < 1000)

    if km_invalido(km_atual):
        km_atual = None
    if km_invalido(km_anterior):
        km_anterior = None

    km_rodado = None
    if km_anterior is not None and km_atual is not None:
        km_rodado = km_atual - km_anterior

    placa_bruta = extrair_campo("placa", infCpl)
    placa_normalizada = re.sub(r"[\s\-]", "", placa_bruta).upper() if placa_bruta else None

    dados = {
        "arquivo": caminho_xml,
        "data_emissao": ide.find("nfe:dhEmi", NS).text if ide is not None and ide.find("nfe:dhEmi", NS) is not None else None,
        "posto": emit.find("nfe:xNome", NS).text if emit is not None and emit.find("nfe:xNome", NS) is not None else None,
        "empresa": dest.find("nfe:xNome", NS).text if dest is not None and dest.find("nfe:xNome", NS) is not None else None,
        "combustivel": combustivel_nome,
        "litros": litros_total if litros_total else None,
        "valor_total": valor_pago,
        "tipo_veiculo": extrair_campo("tipo_veiculo", infCpl),
        "placa": placa_normalizada,
        "motorista": extrair_campo("motorista", infCpl),
        "km_anterior": km_anterior,
        "km_atual": km_atual,
        "km_rodado": km_rodado,
        "media_km_l": media,
        "duplicado": bool(eh_resumo_duplicado),
    }
    return dados
