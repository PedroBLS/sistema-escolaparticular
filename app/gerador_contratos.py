"""
Módulo para geração automática de contratos em PDF
Baseado nos modelos de contrato fornecidos pelo usuário
"""

from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import os

class GeradorContratos:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Dados da empresa (ÍMPETUS INSTITUTO DE EDUCAÇÃO)
        self.dados_empresa = {
            'nome': 'ÍMPETUS INSTITUTO DE EDUCAÇÃO',
            'cnpj': '36.207.755/0001-09',
            'endereco': 'SCLN 103 Bloco B Sala 7',
            'representante': 'ISABELLE LIMA BRANDÃO',
            'nacionalidade': 'brasileira',
            'estado_civil': 'divorciada',
            'rg': '1040143 SSP/DF',
            'cpf': '399.051.101-78',
            'endereco_representante': 'SQN 204 Bloco J Ap. 501, CEP: 70733-100',
            'pix': '36.207.755/0001-09',
            'agencia': '2991',
            'conta': '11.075242-7',
            'banco': 'Santander'
        }
        
        # Configurações dos tipos de contrato
        self.tipos_contrato = {
            'aula_avulsa': {
                'nome': 'AULA PARTICULAR',
                'objeto': 'prestação de serviço de aula particular',
                'duracao': '1 (uma) hora aula',
                'valor_base': 100.00,
                'valor_1h30': 142.50,
                'valor_2h': 180.00,
                'prazo': 'indeterminado',
                'forma_pagamento': 'até o dia 08 (oito) de cada mês'
            },
            'pacote_10_aulas': {
                'nome': 'AULA PARTICULAR',
                'objeto': 'prestação de serviço de 10 aulas particulares',
                'duracao': '1 (uma) hora aula',
                'valor': 950.00,
                'valor_por_hora': 95.00,
                'prazo': '6 meses',
                'forma_pagamento': 'antecipado na assinatura do Contrato'
            },
            'pacote_20_aulas': {
                'nome': 'AULA PARTICULAR',
                'objeto': 'prestação de serviço de 20 aulas particulares',
                'duracao': '1 (uma) hora aula',
                'valor': 1800.00,
                'valor_por_hora': 90.00,
                'prazo': '12 meses',
                'forma_pagamento': 'antecipado na assinatura do Contrato'
            },
            'pacote_30_aulas': {
                'nome': 'AULA PARTICULAR',
                'objeto': 'prestação de serviço de 30 aulas particulares',
                'duracao': '1 (uma) hora aula',
                'valor': 2550.00,
                'valor_por_hora': 85.00,
                'prazo': '12 meses',
                'forma_pagamento': 'antecipado na assinatura do Contrato'
            },
            'assinatura_gold': {
                'nome': 'AULA PARTICULAR',
                'objeto': 'prestação de serviço de aula particular',
                'duracao': '1 (uma) hora aula',
                'modalidades': {
                    '1_8_aulas': {'valor': 680.00, 'descricao': 'De 1 a 8 aulas por mês', 'adicional': 85.00},
                    '14_aulas': {'valor': 1120.00, 'descricao': 'De 14 aulas por mês', 'adicional': 80.00},
                    '20_aulas': {'valor': 1500.00, 'descricao': 'De 20 aulas por mês', 'adicional': 75.00}
                },
                'prazo': 'indeterminado',
                'forma_pagamento': 'até o dia 08 (oito) de cada mês'
            },
            'aula_grupo': {
                'nome': 'AULA PARTICULAR EM GRUPO',
                'objeto': 'prestação de serviço de aula particular em grupo',
                'duracao': '1 (uma) hora aula',
                'valor_base': 80.00,
                'prazo': 'conforme acordado',
                'forma_pagamento': 'conforme acordado'
            }
        }

    def setup_custom_styles(self):
        """Configura estilos personalizados para o documento"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        self.clause_style = ParagraphStyle(
            'CustomClause',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Bold'
        )

    def gerar_contrato_avulso(self, dados_contrato, caminho_arquivo):
        """Gera contrato para aula avulsa"""
        doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4)
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE CONSUMO – AULA PARTICULAR", self.title_style))
        story.append(Paragraph("ÍMPETUS INSTITUTO DE EDUCAÇÃO", self.subtitle_style))
        story.append(Spacer(1, 20))
        
        # Partes do contrato
        partes_texto = self._gerar_texto_partes(dados_contrato)
        story.append(Paragraph(partes_texto, self.body_style))
        story.append(Spacer(1, 20))
        
        # Cláusulas específicas para aula avulsa
        clausulas = self._gerar_clausulas_avulsa(dados_contrato)
        for clausula in clausulas:
            story.append(Paragraph(clausula, self.body_style))
            story.append(Spacer(1, 10))
        
        # Assinaturas
        assinaturas = self._gerar_assinaturas(dados_contrato)
        story.append(Spacer(1, 30))
        story.append(Paragraph(assinaturas, self.body_style))
        
        doc.build(story)
        return caminho_arquivo

    def gerar_contrato_pacote(self, dados_contrato, tipo_pacote, caminho_arquivo):
        """Gera contrato para pacote de aulas (10 ou 20 aulas)"""
        doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4)
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE CONSUMO – AULA PARTICULAR", self.title_style))
        story.append(Paragraph("ÍMPETUS INSTITUTO DE EDUCAÇÃO", self.subtitle_style))
        story.append(Spacer(1, 20))
        
        # Partes do contrato
        partes_texto = self._gerar_texto_partes(dados_contrato)
        story.append(Paragraph(partes_texto, self.body_style))
        story.append(Spacer(1, 20))
        
        # Cláusulas específicas para pacote
        clausulas = self._gerar_clausulas_pacote(dados_contrato, tipo_pacote)
        for clausula in clausulas:
            story.append(Paragraph(clausula, self.body_style))
            story.append(Spacer(1, 10))
        
        # Assinaturas
        assinaturas = self._gerar_assinaturas(dados_contrato)
        story.append(Spacer(1, 30))
        story.append(Paragraph(assinaturas, self.body_style))
        
        doc.build(story)
        return caminho_arquivo

    def _gerar_texto_partes(self, dados):
        """Gera o texto das partes do contrato"""
        # Formatação dos nomes dos alunos
        if len(dados['alunos']) == 1:
            alunos_texto = dados['alunos'][0]['nome']
        else:
            nomes_alunos = [aluno['nome'] for aluno in dados['alunos']]
            alunos_texto = ' e '.join(nomes_alunos)
        
        texto = f"""
        <b>{self.dados_empresa['nome']}</b>, pessoa jurídica inscrita no CNPJ Nº {self.dados_empresa['cnpj']}, 
        instalada no {self.dados_empresa['endereco']}, neste ato representado por <b>{self.dados_empresa['representante']}</b>, 
        {self.dados_empresa['nacionalidade']}, {self.dados_empresa['estado_civil']}, portadora do RG nº {self.dados_empresa['rg']} 
        e CPF nº {self.dados_empresa['cpf']}, residente e domiciliada no {self.dados_empresa['endereco_representante']}, 
        doravante denominada <b>CONTRATADO</b>
        <br/><br/>
        <b>{dados['responsavel']['nome']}</b>, {dados['responsavel'].get('nacionalidade', 'brasileira')}, 
        {dados['responsavel'].get('estado_civil', '')}, portador(a) do RG nº {dados['responsavel']['rg']} 
        e inscrito(a) no CPF nº {dados['responsavel']['cpf']}, com endereço eletrônico {dados['responsavel']['email']}, 
        número telefônico {dados['responsavel']['telefone']}, residente e domiciliado(a) no {dados['responsavel']['endereco']}, 
        doravante denominado <b>CONTRATANTE</b>, vem, por meio deste contrato, representar seu(s) filho(s) <b>{alunos_texto}</b>
        <br/><br/>
        As <b>PARTES</b> acima identificadas têm, entre si, justo e acordado, o presente Contrato De Prestação De Serviço, 
        regido pelas cláusulas e condições descritas a seguir expostas, as quais mutuamente aceitam e se outorgam:
        """
        return texto

    def _gerar_clausulas_avulsa(self, dados):
        """Gera as cláusulas específicas para contrato de aula avulsa"""
        clausulas = []
        
        # DO OBJETO
        clausulas.append("""
        <b>DO OBJETO</b><br/>
        <b>CLÁUSULA PRIMEIRA:</b> O presente contrato tem como OBJETO a prestação de serviço de aula particular, 
        seja na sala de aula da ÍMPETUS INSTITUTO DE EDUCAÇÃO ou na própria residência do aluno, pela empresa 
        ÍMPETUS INSTITUTO DE EDUCAÇÃO ao CONTRATANTE pela duração de 1 (uma) hora aula sendo realizado quantas 
        vezes forem combinadas, seja via WhatsApp, e-mails ou outro mecanismo escrito.
        """)
        
        # DAS AULAS
        clausulas.append("""
        <b>DAS AULAS</b><br/>
        <b>CLÁUSULA SEGUNDA:</b> Cada aula contratada terá a duração de 1 (uma) hora a serem realizadas quantas 
        vezes por semana forem necessárias de forma avulsa com dia e horário previamente convencionados por escrito.<br/>
        <b>Parágrafo Único.</b> O tempo que exceder a duração prevista no caput será cobrada de forma proporcional.
        """)
        
        # DAS ALTERAÇÕES E REMARCAÇÕES
        clausulas.append("""
        <b>DAS ALTERAÇÕES E REMARCAÇÕES DAS AULAS</b><br/>
        <b>CLÁUSULA TERCEIRA:</b> Caso o CONTRATANTE:<br/>
        A) Deseje alterar o dia ou horário da aula;<br/>
        B) Falte a aula;<br/>
        C) Cancele a aula.<br/>
        Este ficará obrigado a comunicar o CONTRATADO, por escrito, com antecedência mínima de 24 (vinte e quatro) horas.<br/>
        <b>Parágrafo Único.</b> Caso o prazo da CLÁUSULA acima não seja cumprido, o CONTRATANTE deverá arcar com o 
        valor da aula, salvo se este apresentar um atestado médico, situação em que o CONTRATANTE poderá remarcar a 
        aula sem custo adicional.
        """)
        
        # DO PAGAMENTO
        valor_deslocamento = "R$ 15,00 (quinze reais)" if not dados.get('mora_plano_piloto', False) else ""
        texto_deslocamento = f"Caso o aluno não resida nem na Asa Sul, Asa Norte, o CONTRATANTE deverá pagar, além do valor disposto no caput, o valor de {valor_deslocamento} a título de indenização pelo deslocamento do professor." if valor_deslocamento else ""
        
        clausulas.append(f"""
        <b>DO PAGAMENTO</b><br/>
        <b>CLÁUSULA DÉCIMA:</b> Pela realização dos serviços descritos neste contrato, o CONTRATANTE remunerará o 
        CONTRATADO com o valor de R$ 100,00 (cem reais) hora/aula caso o aluno compre apenas 1h de aula, com o valor 
        de R$ 142,50 (cento e quarenta e dois reais e cinquenta centavos) caso o aluno contrate uma hora e meia de 
        aula avulsa no mesmo dia, com o valor de R$ 180,00 (cento e oitenta reais) caso o aluno contrate 2h de aula 
        no mesmo dia. A serem pagos por transferência bancária, boleto ou pix.<br/>
        <b>Parágrafo Primeiro.</b> {texto_deslocamento}<br/>
        <b>Parágrafo Segundo.</b> O pagamento dos valores descritos na CLÁUSULA acima será realizado até o dia 08 
        (oito) de cada mês. Caso o dia do pagamento venha a cair em feriado ou final de semana, será considerada a 
        data do vencimento no próximo dia útil subsequente.<br/>
        <b>Parágrafo Terceiro.</b> Os valores deverão ser depositados na seguinte conta bancária:<br/>
        I. CONTRATADO:<br/>
        a. PIX (CNPJ): {self.dados_empresa['pix']}<br/>
        b. Agência: {self.dados_empresa['agencia']}<br/>
        Conta: {self.dados_empresa['conta']}<br/>
        Instituição: {self.dados_empresa['banco']}<br/>
        Nome da Empresa: {self.dados_empresa['representante']}
        """)
        
        # DA VIGÊNCIA
        data_inicio = dados.get('data_inicio', date.today()).strftime('%d/%m/%Y')
        clausulas.append(f"""
        <b>DA VIGÊNCIA</b><br/>
        <b>CLÁUSULA DÉCIMA SEGUNDA:</b> O presente Contrato se iniciará em {data_inicio} e terá prazo indeterminado.
        """)
        
        return clausulas

    def _gerar_clausulas_pacote(self, dados, tipo_pacote):
        """Gera as cláusulas específicas para contrato de pacote de aulas"""
        clausulas = []
        config = self.tipos_contrato[tipo_pacote]
        
        num_aulas = "10" if tipo_pacote == "pacote_10_aulas" else "20"
        valor_total = f"R$ {config['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        valor_hora = f"R$ {config['valor_por_hora']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        prazo_meses = config['prazo']
        
        # DO OBJETO
        clausulas.append(f"""
        <b>DO OBJETO</b><br/>
        <b>CLÁUSULA PRIMEIRA:</b> O presente contrato tem como OBJETO a prestação de serviço de {num_aulas} aulas 
        particulares, seja na sala de aula da ÍMPETUS INSTITUTO DE EDUCAÇÃO ou na própria residência do aluno, 
        pela empresa ÍMPETUS INSTITUTO DE EDUCAÇÃO ao CONTRATANTE, conforme convencionado seja via WhatsApp, 
        e-mails ou outro mecanismo escrito, pela duração de 1 (uma) hora aula.
        """)
        
        # DAS AULAS
        clausulas.append(f"""
        <b>DAS AULAS</b><br/>
        <b>CLÁUSULA SEGUNDA:</b> Cada aula contratada terá a duração de 1 (uma) hora, com dia e horário previamente 
        convencionados por escrito, a serem realizadas da seguinte forma:<br/>
        {num_aulas} aulas → {valor_total} ({valor_hora}/h) → Válido por {prazo_meses}<br/>
        <b>Parágrafo Único.</b> O tempo que exceder a duração prevista no caput será cobrada de forma proporcional.
        """)
        
        # DO PAGAMENTO
        valor_extenso = self._numero_por_extenso(config['valor'])
        clausulas.append(f"""
        <b>DO PAGAMENTO</b><br/>
        <b>CLÁUSULA DÉCIMA:</b> Pela realização dos serviços descritos neste contrato, o CONTRATANTE remunerará o 
        CONTRATADO com o valor de {valor_total} ({valor_extenso}), a serem pagos de forma antecipada por transferência 
        bancária, boleto ou pix.<br/>
        <b>Parágrafo Primeiro.</b> Caso o aluno não resida na Asa Sul ou na Asa Norte, o CONTRATANTE deverá pagar, 
        além do valor disposto no caput, o valor de R$ 15,00 (quinze reais) a título de indenização pelo deslocamento 
        do professor.<br/>
        <b>Parágrafo Segundo.</b> O pagamento dos valores descritos na CLÁUSULA acima será realizado na assinatura do Contrato.<br/>
        <b>Parágrafo Terceiro.</b> Os valores deverão ser depositados na seguinte conta bancária:<br/>
        I. CONTRATADO:<br/>
        a. PIX (CNPJ): {self.dados_empresa['pix']}<br/>
        b. Agência: {self.dados_empresa['agencia']}<br/>
        Conta: {self.dados_empresa['conta']}<br/>
        Instituição: {self.dados_empresa['banco']}<br/>
        Nome da Empresa: {self.dados_empresa['representante']}
        """)
        
        # DA VIGÊNCIA
        data_inicio = dados.get('data_inicio', date.today()).strftime('%d/%m/%Y')
        clausulas.append(f"""
        <b>DA VIGÊNCIA</b><br/>
        <b>CLÁUSULA DÉCIMA SEGUNDA:</b> O presente Contrato se iniciará em {data_inicio} e terá prazo de {prazo_meses}.
        """)
        
        return clausulas

    def _gerar_assinaturas(self, dados):
        """Gera a seção de assinaturas"""
        data_hoje = datetime.now().strftime('%d de %B de %Y')
        
        texto = f"""
        E, por assim estarem de acordo, as PARTES firmam o presente Contrato, em 02 (duas) vias de igual teor, 
        na presença das testemunhas abaixo assinadas, para que produza seus devidos efeitos legais.
        <br/><br/>
        Brasília, {data_hoje}.
        <br/><br/><br/>
        ____________________________________________<br/>
        ({self.dados_empresa['nome']})<br/>
        CONTRATADO<br/>
        {self.dados_empresa['representante']}<br/>
        Representante
        <br/><br/><br/>
        ____________________________________________<br/>
        {dados['responsavel']['nome']}<br/>
        CONTRATANTE
        <br/><br/><br/>
        ____________________________________________<br/>
        PEDRO BRANDÃO LEAL DOS SANTOS<br/>
        RG: 3261021<br/>
        Testemunha 1
        <br/><br/><br/>
        ____________________________________________<br/>
        ELITON MARCELO DE ALMEIDA<br/>
        RG: 1202198<br/>
        Testemunha 2
        """
        return texto

    def _numero_por_extenso(self, valor):
        """Converte número para extenso (implementação básica)"""
        valores_extenso = {
            950.00: "novecentos e cinquenta reais",
            1800.00: "mil e oitocentos reais",
            2550.00: "dois mil, quinhentos e cinquenta reais",
            680.00: "seiscentos e oitenta reais",
            1120.00: "mil, cento e vinte reais",
            1500.00: "mil e quinhentos reais",
            100.00: "cem reais",
            142.50: "cento e quarenta e dois reais e cinquenta centavos",
            180.00: "cento e oitenta reais"
        }
        return valores_extenso.get(valor, f"{valor:.2f} reais")

    def gerar_contrato_assinatura_gold(self, dados_contrato, modalidade, caminho_arquivo):
        """Gera contrato para assinatura gold"""
        doc = SimpleDocTemplate(caminho_arquivo, pagesize=A4)
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE CONSUMO – AULA PARTICULAR", self.title_style))
        story.append(Paragraph("ÍMPETUS INSTITUTO DE EDUCAÇÃO", self.subtitle_style))
        story.append(Spacer(1, 20))
        
        # Partes do contrato
        partes_texto = self._gerar_texto_partes(dados_contrato)
        story.append(Paragraph(partes_texto, self.body_style))
        story.append(Spacer(1, 20))
        
        # Cláusulas específicas para assinatura gold
        clausulas = self._gerar_clausulas_assinatura_gold(dados_contrato, modalidade)
        for clausula in clausulas:
            story.append(Paragraph(clausula, self.body_style))
            story.append(Spacer(1, 10))
        
        # Assinaturas
        assinaturas = self._gerar_assinaturas(dados_contrato)
        story.append(Spacer(1, 30))
        story.append(Paragraph(assinaturas, self.body_style))
        
        doc.build(story)
        return caminho_arquivo

    def _gerar_clausulas_assinatura_gold(self, dados, modalidade):
        """Gera as cláusulas específicas para contrato de assinatura gold"""
        clausulas = []
        config = self.tipos_contrato['assinatura_gold']
        modalidade_info = config['modalidades'][modalidade]
        
        # DO OBJETO
        clausulas.append("""
        <b>DO OBJETO</b><br/>
        <b>CLÁUSULA PRIMEIRA:</b> O presente contrato tem como OBJETO a prestação de serviço de aula particular, 
        seja na sala de aula da ÍMPETUS INSTITUTO DE EDUCAÇÃO ou na própria residência do aluno, pela empresa 
        ÍMPETUS INSTITUTO DE EDUCAÇÃO ao CONTRATANTE pelo período em que perdurar a assinatura deste, pela 
        duração de 1 (uma) hora aula.
        """)
        
        # MODALIDADE DE ASSINATURA
        valor_formatado = f"R$ {modalidade_info['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        adicional_formatado = f"R$ {modalidade_info['adicional']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        if modalidade == '1_8_aulas':
            clausulas.append(f"""
            <b>CLÁUSULA SEGUNDA:</b> O CONTRATANTE adquiriu a seguinte modalidade de assinatura:<br/>
            • De 1 a 8 aulas por mês o valor cheio fica de {valor_formatado} (seiscentos e oitenta reais)<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;o (da 9ª a 13ª aulas serão acrescidos {adicional_formatado} por aula)<br/>
            <b>Parágrafo Único.</b> No presente contrato, o número de aulas a que o CONTRATANTE tem direito, 
            conforme a modalidade de assinatura escolhida, poderá ser dividida pelo número de filhos, de forma 
            que cada um terá a mesma quantidade de aulas.
            """)
        elif modalidade == '14_aulas':
            clausulas.append(f"""
            <b>CLÁUSULA SEGUNDA:</b> O CONTRATANTE adquiriu a seguinte modalidade de assinatura:<br/>
            • De 14 aulas por mês o valor cheio fica de {valor_formatado} (mil, cento e vinte reais)<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;o (de 15ª a 19ª aulas serão acrescidos {adicional_formatado} por aula)<br/>
            <b>Parágrafo Único.</b> No presente contrato, o número de aulas a que o CONTRATANTE tem direito, 
            conforme a modalidade de assinatura escolhida, poderá ser dividida pelo número de filhos, de forma 
            que cada um terá a mesma quantidade de aulas.
            """)
        else:  # 20_aulas
            clausulas.append(f"""
            <b>CLÁUSULA SEGUNDA:</b> O CONTRATANTE adquiriu a seguinte modalidade de assinatura:<br/>
            • De 20 aulas por mês o valor cheio fica de {valor_formatado} (mil e quinhentos reais)<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;o (da 21ª aula para cima serão acrescidos {adicional_formatado} por aula)<br/>
            <b>Parágrafo Único.</b> No presente contrato, o número de aulas a que o CONTRATANTE tem direito, 
            conforme a modalidade de assinatura escolhida, poderá ser dividida pelo número de filhos, de forma 
            que cada um terá a mesma quantidade de aulas.
            """)
        
        # DAS AULAS
        clausulas.append("""
        <b>DAS AULAS</b><br/>
        <b>CLÁUSULA TERCEIRA:</b> Cada aula contratada terá a duração de 1 (uma) hora a serem realizadas em 
        dia e horário previamente convencionados e executadas na forma da opção selecionada pelo CONTRATANTE, 
        conforme disposto na CLÁUSULA SEGUNDA.<br/>
        <b>Parágrafo Primeiro.</b> O tempo que exceder a duração prevista no caput será cobrado de forma proporcional.<br/>
        <b>Parágrafo Segundo.</b> Caso o CONTRATANTE não usufrua de todas as aulas que tem direito, continuará 
        pagando o valor inteiro da assinatura.
        """)
        
        # DAS ALTERAÇÕES E REMARCAÇÕES
        clausulas.append("""
        <b>DAS ALTERAÇÕES E REMARCAÇÕES DAS AULAS</b><br/>
        <b>CLÁUSULA QUARTA:</b> Caso o CONTRATANTE:<br/>
        A) Deseje alterar o dia ou horário da aula;<br/>
        B) Falte a aula;<br/>
        C) Cancele a aula.<br/>
        Este ficará obrigado a comunicar o CONTRATADO, por escrito, com antecedência mínima de 24 (vinte e quatro) horas.<br/>
        <b>Parágrafo Primeiro.</b> Caso o prazo da CLÁUSULA acima não seja cumprido, considerar-se-á como aula dada, 
        não sendo cabível reposição e nem restituição dos valores pagos.<br/>
        <b>Parágrafo Segundo.</b> Respeitado o prazo do caput, o CONTRATANTE será o responsável por reagendar as 
        aulas do seu interesse, exclusivamente com o CONTRATADO. Caso não o faça no prazo de 1 semana, será devido 
        o pagamento integral das aulas e não será cabível a restituição dos mesmos.
        """)
        
        # DO PAGAMENTO
        valor_extenso = self._numero_por_extenso(modalidade_info['valor'])
        clausulas.append(f"""
        <b>DO PAGAMENTO</b><br/>
        <b>CLÁUSULA DÉCIMA PRIMEIRA:</b> Pela realização dos serviços descritos neste contrato, o CONTRATANTE 
        remunerará o CONTRATADO com o valor descrito na CLÁUSULA SEGUNDA, a serem pagos por transferência bancária, 
        boleto ou pix.<br/>
        <b>Parágrafo Primeiro.</b> O pagamento dos valores descritos na CLÁUSULA acima será realizado até o dia 08 
        (oito) de cada mês, independentemente do dia da aquisição da assinatura. Caso o dia do pagamento venha a 
        cair em feriado ou final de semana, será considerada a data do vencimento no próximo dia útil subsequente.<br/>
        <b>Parágrafo Segundo.</b> Os valores deverão ser depositados na seguinte conta bancária:<br/>
        I. CONTRATADO:<br/>
        a. PIX (CNPJ): {self.dados_empresa['pix']}<br/>
        b. Agência: {self.dados_empresa['agencia']}<br/>
        Conta: {self.dados_empresa['conta']}<br/>
        Instituição: {self.dados_empresa['banco']}<br/>
        Nome da Empresa: {self.dados_empresa['representante']}<br/>
        <b>Parágrafo Terceiro.</b> Caso o aluno não resida na Asa Sul ou na Asa Norte, o CONTRATANTE deverá pagar, 
        além do valor disposto no caput, o valor de R$ 15,00 (quinze reais) a título de indenização pelo deslocamento 
        do professor.
        """)
        
        # DA VIGÊNCIA
        data_inicio = dados.get('data_inicio', date.today()).strftime('%d/%m/%Y')
        clausulas.append(f"""
        <b>DA VIGÊNCIA</b><br/>
        <b>CLÁUSULA DÉCIMA TERCEIRA:</b> O presente Contrato se iniciará em {data_inicio} e terá prazo indeterminado, 
        vigendo-se até que o CONTRATANTE cancele sua assinatura.
        """)
        
        return clausulas

    def gerar_contrato_automatico(self, responsavel, alunos, tipo_plano, valor_total, data_inicio, validade, observacoes=""):
        """
        Gera contrato automaticamente baseado nos dados fornecidos
        
        Args:
            responsavel: Objeto Responsavel do banco de dados
            alunos: Lista de objetos Aluno
            tipo_plano: String com o tipo de plano
            valor_total: Valor total do contrato
            data_inicio: Data de início do contrato
            validade: Data de validade do contrato
            observacoes: Observações adicionais
        
        Returns:
            Caminho do arquivo PDF gerado
        """
        
        # Preparar dados para o contrato
        dados_contrato = {
            'responsavel': {
                'nome': responsavel.nome,
                'cpf': responsavel.cpf,
                'rg': responsavel.rg,
                'telefone': responsavel.telefone,
                'email': responsavel.email,
                'endereco': responsavel.endereco,
                'estado_civil': responsavel.estado_civil or '',
                'nacionalidade': responsavel.nacionalidade or 'brasileira'
            },
            'alunos': [
                {
                    'nome': aluno.nome,
                    'cpf': aluno.cpf,
                    'rg': aluno.rg
                } for aluno in alunos
            ],
            'tipo_plano': tipo_plano,
            'valor_total': valor_total,
            'data_inicio': data_inicio,
            'validade': validade,
            'observacoes': observacoes,
            'mora_plano_piloto': any(aluno.mora_plano_piloto for aluno in alunos)
        }
        
        # Determinar tipo de contrato e gerar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"contrato_{responsavel.id}_{timestamp}.pdf"
        caminho_arquivo = os.path.join("static", "contratos", nome_arquivo)
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        
        if tipo_plano == "Aula Avulsa":
            return self.gerar_contrato_avulso(dados_contrato, caminho_arquivo)
        elif tipo_plano == "Pacote 10 aulas":
            return self.gerar_contrato_pacote(dados_contrato, "pacote_10_aulas", caminho_arquivo)
        elif tipo_plano == "Pacote 20 aulas":
            return self.gerar_contrato_pacote(dados_contrato, "pacote_20_aulas", caminho_arquivo)
        elif tipo_plano == "Pacote 30 aulas":
            return self.gerar_contrato_pacote(dados_contrato, "pacote_30_aulas", caminho_arquivo)
        elif tipo_plano.startswith("Assinatura Gold"):
            # Extrair modalidade da string do tipo_plano
            if "1-8 aulas" in tipo_plano:
                modalidade = "1_8_aulas"
            elif "14 aulas" in tipo_plano:
                modalidade = "14_aulas"
            elif "20 aulas" in tipo_plano:
                modalidade = "20_aulas"
            else:
                modalidade = "1_8_aulas"  # padrão
            return self.gerar_contrato_assinatura_gold(dados_contrato, modalidade, caminho_arquivo)
        else:
            # Para outros tipos, usar modelo básico
            return self.gerar_contrato_avulso(dados_contrato, caminho_arquivo)


# Função auxiliar para uso nas rotas Flask
def gerar_contrato_pdf(responsavel, alunos, tipo_plano, valor_total, data_inicio, validade, observacoes=""):
    """
    Função auxiliar para gerar contrato PDF
    Para ser usada nas rotas Flask
    """
    gerador = GeradorContratos()
    return gerador.gerar_contrato_automatico(
        responsavel, alunos, tipo_plano, valor_total, 
        data_inicio, validade, observacoes
    )
