#coding: utf-8
# Matheus da Cunha Melo Almeida
# 115210030
# matheus.almeida@ccc.ufcg.edu.br
# BitTrade
# Servidor
# Para o correto funcionamento, deve se ter instalado
# na máquina a biblioteca Bitcoin-Python (https://github.com/laanwj/bitcoin-python) e
# o software Bitcoind (https://degreesofzero.com/article/installing-bitcoind-on-ubuntu.html)
import socket
import sqlite3
import thread
import bitcoinrpc

def dbConnect(): # Conexão a database
	conn = sqlite3.connect('database.db')
	c = conn.cursor()
	return c,conn

def cadastro(nome,senha): # Função de cadastro
	c,conn = dbConnect() # Conecta a database
	ex = c.execute('select nome from users where nome="%s"' % nome) # Busca um usuário com o nome informado
	ex = c.fetchone()
	if ex != None: # Caso já exista, retornar 'jc' (já cadastrado)
		return 'jc'
	else: # Caso não exista, cadastrar.
		c.execute('insert into users(nome,pass,reais,btc) values("%s","%s",0,0)' % (nome,senha))
		conn.commit()
		return 'sucesso'

def login(nome,senha): # Função de login
	c,conn = dbConnect()
	ex = c.execute('select nome from users where nome="%s"' % nome) # Busca o usuário com o nome informado
	ex = c.fetchone()
	if ex == None: # Caso não exista, retornar 'naocadastrado'
		return 'naocadastrado'
	else: # Caso exista, verificar se a senha está correta
		ex = c.execute('select pass from users where nome="%s" and pass="%s"' % (nome,senha))
		ex = c.fetchone()
		if ex == None: # Caso esteja incorreta, retornar 'usuariosenha'
			return 'usuariosenha'
		else: # Caso esteja correta, retornar 'sucesso'
			return 'sucesso'

def cancelar(data): # Função para cancelar compras ou vendas
	if len(data) < 3:
		# Testar se o comando realmente está completo
		return 'Uso incorreto do comando.'
	try:
		# Testar se o comando realmente está correto
		qntBTC = float(data[2])
		preco = float(data[3])
	except ValueError:
		return 'Uso incorreto do comando.'
	c,conn = dbConnect()
	user = data[4]
	if data[1] == 'compra': # Caso for uma compra, procurar a compra existente
		ex = c.execute('select * from compras where preco = %.2f and usuario = "%s" and qntBTC = %.8f limit 1'%(preco,user,qntBTC))
		ex = ex.fetchone()
		print ex
		if ex == None: # Caso não exista uma compra com os parâmetros, retornar:
			return 'Nenhuma compra em seu nome encontrada com estes critérios.'
		else: # Caso haja, cancelar a compra
			c.execute('delete from compras where preco = %.2f and usuario = "%s" and qntBTC = %.8f limit 1'%(preco,user,qntBTC))
			c.execute('update users set reais = reais + %.2f' % (preco*qntBTC))
			conn.commit()
			return 'Cancelamento efetuado com sucesso.'
	elif data[1] == 'venda': # Se for uma venda, executar a mesma tarefa
		ex = c.execute('select * from vendas where preco = %.2f and usuario = "%s" and qntBTC = %.8f limit 1'%(preco,user,qntBTC))
		ex = ex.fetchone()
		print ex
		if ex == None:
			return 'Nenhuma venda em seu nome encontrada com estes critérios.'
		else:
			c.execute('delete from vendas where preco = %.2f and usuario = "%s" and qntBTC = %.8f limit 1'%(preco,user,qntBTC))
			c.execute('update users set btc = btc + %.8f' % qntBTC)
			conn.commit()
			return 'Cancelamento efetuado com sucesso.'
	else:
		return 'Uso inadequado do comando.'


def comprar(data): # Função para comprar
	data.pop(0)
	c,conn = dbConnect()
	try:
		# Testar se o comando está correto
		float(data[1])
		float(data[2])
	except ValueError:
		return 'Uso incorreto do comando.'
	if len(data) < 3:
		# Testar se o comando realmente está completo
		return 'Uso incorreto do comando.'
	else: # Se estiver, executar verificações
		nome = data[0]
		qntBTC = float(data[1])
		preco = float(data[2])
		ex = c.execute('select reais from users where nome = "%s"' % nome)
		saldoComprador = ex.fetchone()
		saldoComprador = saldoComprador[0]
		if saldoComprador < float(preco) * float(qntBTC):
			# Caso o usuário não tenha dinheiro suficiente, informar.
			return 'Saldo insuficiente.'
		else:
			# Caso tenha, obter saldo do comprador após a venda e procurar um vendedor.
			novoSaldoComprador = saldoComprador - (qntBTC * preco)
			ex = c.execute('select usuario from vendas where preco = %.2f and usuario != "%s" limit 1' % (preco,nome))
			ex = ex.fetchone()
			if ex != None:
				# Caso haja um usuario vendendo no preço informado e não seja o comprador, 
				# obter informações do vendedor e do comprador.
				vendedor = ex[0]
				ex = c.execute('select qntBTC from vendas where preco = %.2f and usuario = "%s" limit 1' % (preco,vendedor))
				ex = ex.fetchone()
				qntAVenda = ex[0]
				ex = c.execute('select reais from users where nome = "%s"' % vendedor)
				saldoVendedor = ex.fetchone()
				saldoVendedor = saldoVendedor[0]
				novoSaldoVendedor = saldoVendedor + (qntBTC * preco)
				if qntAVenda < qntBTC:
					# Caso a quantidade a venda seja menor que a quantidade pedida, 
					# fazer a compra, deletar a ordem de venda e chamar a função novamente 
					# com o restante de Bitcoins como atributo.
					novoSaldoComprador = saldoComprador - (qntAVenda * preco)
					novoSaldoVendedor = saldoVendedor + (qntAVenda * preco)
					ex = c.execute('select btc from users where nome = "%s"' % nome)
					novoSaldoBTC = ex.fetchone()
					novoSaldoBTC = novoSaldoBTC[0] + qntAVenda
					data2 = ['comprar',nome, qntBTC - qntAVenda, preco]
					c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoBTC,nome))
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoComprador,nome))
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoVendedor,vendedor))
					c.execute('delete from vendas where usuario = "%s" and preco = %.2f limit 1' % (vendedor,preco))
					conn.commit()
					comprar(data2)
					return 'Ordem de compra realizada com sucesso.'
				elif qntAVenda == qntBTC:
					# Caso a quantidade a venda seja igual a quantidade de Bitcoins pedida,
					# realizar a compra e deletar a ordem de venda.
					ex = c.execute('select btc from users where nome = "%s"' % nome)
					novoSaldoBTC = ex.fetchone()
					novoSaldoBTC = novoSaldoBTC[0] + qntAVenda
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoComprador,nome))
					c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoBTC,nome))
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoVendedor,vendedor))
					c.execute('delete from vendas where usuario = "%s" and preco = "%.2f" limit 1' % (vendedor,preco))
					conn.commit()
					return 'Ordem de compra realizada com sucesso.'
				elif qntAVenda > qntBTC:
					# Caso a quantidade a venda seja maior que a quantidade de Bitcoins pedida,
					# Simplesmente realizar a compra.
					ex = c.execute('select btc from users where nome = "%s"' % nome)
					novoSaldoBTC = ex.fetchone()
					novoSaldoBTC = novoSaldoBTC[0] + qntBTC
					c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoBTC,nome))
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoComprador,nome))
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoVendedor,vendedor))
					c.execute('update vendas set qntBTC	= %.8f where usuario = "%s" and preco = "%.2f" limit 1' % (qntAVenda - qntBTC,vendedor,preco))
					conn.commit()
					return 'Ordem de compra realizada com sucesso.'
			else:
				# Caso não haja um usuário vendendo ao preço informado, 
				# abrir uma nova ordem de compra.
				c.execute('insert into compras(usuario,qntBTC,preco) values("%s",%.8f,%.2f)' % (nome,qntBTC,preco))
				c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoComprador,nome))
				conn.commit()
				return 'Ordem de compra realizada com sucesso.'
def vender(data):
	data.pop(0)
	c,conn = dbConnect()
	try:
		# Testar se o comando está correto
		float(data[1])
		float(data[2])
	except ValueError:
		return 'Uso incorreto do comando.'
	if len(data) < 3:
		# Testar se o comando realmente está completo
		return 'Uso incorreto do comando.'
	else: # Caso esteja, executar verificações
		nome = data[0]
		qntBTC = float(data[1])
		preco = float(data[2])
		ex = c.execute('select btc from users where nome = "%s"' % nome)
		saldoVendedor = ex.fetchone()
		saldoVendedor = saldoVendedor[0]
		if saldoVendedor < float(qntBTC):
			# Caso o usuário não tenha Bitcoins suficientes, informar.
			return 'Saldo insuficiente.'
		else:
			# Caso tenha, procurar um comprador.
			ex = c.execute('select usuario from compras where preco = %.2f and usuario != "%s" limit 1' % (preco,nome))
			ex = ex.fetchone()
			if ex != None:
				# Caso haja um usuario comprando no preço informado, 
				# obter informações do vendedor e do comprador.
				comprador = ex[0]
				ex = c.execute('select qntBTC from compras where preco = %.2f and usuario = "%s" limit 1' % (preco,comprador))
				ex = ex.fetchone()
				qntACompra = ex[0]
				ex = c.execute('select btc from users where nome = "%s"' % comprador)
				saldoComprador = ex.fetchone()
				saldoComprador = saldoComprador[0]
				novoSaldoVendedor = saldoVendedor - qntBTC
				novoSaldoComprador = saldoComprador + qntBTC
				if qntACompra < qntBTC:
					# Caso a quantidade desejada para a compra seja menor que a quantidade pedida, 
					# fazer a venda, deletar a ordem de compra e chamar a função novamente 
					# com o restante de Bitcoins como atributo.
					novoSaldoComprador = saldoComprador + qntACompra
					novoSaldoVendedor = saldoVendedor - qntACompra
					ex = c.execute('select reais from users where nome = "%s"' % nome)
					novoSaldoReais = ex.fetchone()
					novoSaldoReais = novoSaldoReais[0] - (qntACompra * preco)
					data2 = ['comprar',nome, qntBTC - qntACompra, preco]
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoReais,nome))
					c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoVendedor,nome))
					c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoComprador,comprador))
					c.execute('delete from compras where usuario = "%s" and preco = %.2" limit 1' % (comprador,preco))
					conn.commit()
					vender(data2)
					return 'Ordem de venda realizada com sucesso.'
				elif qntACompra == qntBTC:
					# Caso a quantidade requerida para venda seja igual a quantidade de Bitcoins pedida,
					# realizar a venda e deletar a ordem de compra.
					ex = c.execute('select reais from users where nome = "%s"' % nome)
					novoSaldoReais = ex.fetchone()
					novoSaldoReais = novoSaldoReais[0] + (qntACompra * preco)
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoReais,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoVendedor,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoComprador,comprador))
					c.execute('delete from compras where usuario = "%s" and preco = "%.2f" limit 1' % (comprador,preco))
					conn.commit()
					return 'Ordem de venda realizada com sucesso.'
				elif qntACompra > qntBTC:
					# Caso a quantidade a venda seja maior que a quantidade de Bitcoins pedida,
					# simplesmente realizar a compra.
					ex = c.execute('select reais from users where nome = "%s"' % nome)
					novoSaldoReais = ex.fetchone()
					novoSaldoReais = novoSaldoReais[0] + (qntBTC * preco)
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoReais,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoVendedor,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoComprador,comprador))
					c.execute('update compras set qntBTC = %.8f where usuario = "%s" and preco = "%.2f" limit 1' % (qntACompra - qntBTC,nome,preco))
					conn.commit()
					return 'Ordem de venda realizada com sucesso.'
			else:
				# Caso não haja um usuário comprando ao preço informado, 
				# abrir uma nova ordem de venda.
				novoSaldoVendedor = saldoVendedor - qntBTC
				c.execute('insert into vendas(usuario,qntBTC,preco) values("%s",%.8f,%.2f)' % (nome,qntBTC,preco))
				c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoVendedor,nome))
				conn.commit()
				return 'Ordem de venda realizada com sucesso.'

def compras():
	# Lista de compras
	c,conn = dbConnect() # Conecta com a database
	ex = c.execute('select * from compras') # Seleciona todas as compras da tabela
	ex = ex.fetchall()
	data = ""
	for i in ex:
		for j in i: # Concatena as listas em uma string para envio
			data += str(j)+","
		data += ";"
	if data == "": # Caso não haja compras, retornar o status.
		data = "semCompras"
	return data

def vendas():
	# Lista de vendas
	c,conn = dbConnect() # Conecta a database
	ex = c.execute('select * from vendas')
	ex = ex.fetchall()
	data = ""
	for i in ex: # Concatena as vendas em uma string para envio
		for j in i:
			data += str(j)+","
		data += ";"
	if data == "": # Caso não haja vendas, retornar o status
		data = "semVendas"
	return data

def saldo(nome): # Função de saldo
	c,conn = dbConnect() # Conecta a database
	ex = c.execute('select reais from users where nome = "%s"' % nome) # Procura o saldo em reais do usuário
	reais = ex.fetchone()[0]
	ex = c.execute('select btc from users where nome = "%s"' % nome) # Procura o saldo em Bitcoins do usuário
	saldo = "%s,%s" % (str(reais),str(ex.fetchone()[0]))
	return saldo

def newAddress(nome): # Função para criação de um novo endereç Bitcoin ou retorno do endereço já criado
	bit = bitcoinrpc.connect_to_local()
	c,conn = dbConnect() # Conecta a database
	ex = c.execute('select address from users where nome = "%s"' % nome) # Procura o endeço do usuário
	address = ex.fetchone()
	address = address[0]
	if address == None: # Caso o usuário não tenha um endereço, criar.
		address = bit.getnewaddress(nome)
		c.execute('update users set address = "%s" where nome = "%s"' % (address,nome))
		conn.commit()
		return address
	else: # Caso tenha, apenas retorná-lo
		return address

def deposito(qntBTC,account): # Função de deposito, esta função não é executada pelo client e sim quando um deposito é detectado.
	# A função é disparada quando o servidor recebe a mensagem vinda da página notify.php
	c,conn = dbConnect()
	c.execute('update users set btc = btc + %s where nome = "%s"'%(qntBTC,account)) # Adiciona o saldo na conta
	conn.commit()

def saque(data): # Função de saque
	bit = bitcoinrpc.connect_to_local() # Conecta a carteira local 
	c,conn = dbConnect() # Conecta a database
	if len(data) != 4: # Verifica se o comando está completo
		return 'Uso inadequado do comando.'
	try: # Verifica se o comando está correto
		qntBTC = float(data[1])
	except ValueError:
		return 'Uso inadequado do comando.'
	address = data[2]
	val = bit.validateaddress(address) # Checa se o endereço é válido
	if not val.isvalid:
		return 'Endereço inválido'
	# Caso tudo esteja correto, entra na função:
	nome = data[3]
	ex = c.execute('select btc from users where nome = "%s"'%(nome)) # Obtém o saldo do usuário
	ex = ex.fetchone()[0]
	if (ex-0.0002) < qntBTC:
		return 'Saldo insuficiente'
	else: # Caso o usuário tenha saldo suficiente, enviar para a conta e retirar do saldo
		bit.sendtoaddress(address,qntBTC)
		c.execute('update users set btc = btc - %.8f where nome = "%s"'%(qntBTC+0.0002,nome))
		conn.commit()
		return 'Saque realizado com sucesso.'
		
def clientHandler(clientsocket,address): # Função principal
	print "Conexão de ",address
	data = clientsocket.recv(100)
	print 'Recebido: "%s"' % data
	data = data.split()
	retorno = ""
	# Direcionamentos para as funções corretas:
	if len(data) == 0:
		retorno = "Uso incorreto do comando."
	elif data[0] == 'comprar':
		retorno = comprar(data)
	elif data[0] == 'vender':
		retorno = vender(data)
	elif data[0] == 'cadastro':
		retorno = cadastro(data[1],data[2])
	elif data[0] == 'login':
		retorno = login(data[1],data[2])
	elif data[0] == 'compras':
		retorno = compras()
	elif data[0] == 'vendas':
		retorno = vendas()
	elif data[0] == 'saldo':
		retorno = saldo(data[1])
	elif data[0] == 'depositar':
		retorno = newAddress(data[1]);
	elif data[0] == 'deposito':
		deposito(data[1],data[2])
	elif data[0] == 'cancelar':
		retorno = cancelar(data)
	elif data[0] == 'saque':
		retorno = saque(data)
	clientsocket.sendall(retorno)
	clientsocket.close()
if __name__ == "__main__":
	# Configuração do socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('', 7254))
	serversocket.listen(4)
	while True: # Lida com as conexões
		clientsocket, address = serversocket.accept()
		thread.start_new_thread(clientHandler, (clientsocket, address))
