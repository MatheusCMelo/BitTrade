#coding: utf-8
import socket
import sqlite3
import thread

def dbConnect():
	conn = sqlite3.connect('database.db')
	c = conn.cursor()
	return c,conn
def cadastro(nome,senha):
	c,conn = dbConnect()
	ex = c.execute('select nome from users where nome="%s"' % nome)
	ex = c.fetchone()
	if ex != None:
		return 'jc'
	else:
		c.execute('insert into users(nome,pass,reais,btc) values("%s","%s",0,0)' % (nome,senha))
		conn.commit()
		return 'sucesso'

def login(nome,senha):
	c,conn = dbConnect()
	ex = c.execute('select nome from users where nome="%s"' % nome)
	ex = c.fetchone()
	if ex == None:
		return 'naocadastrado'
	else:
		ex = c.execute('select pass from users where nome="%s" and pass="%s"' % (nome,senha))
		ex = c.fetchone()
		if ex == None:
			return 'usuariosenha'
		else:
			return 'sucesso'

def comprar(data):
	data.pop(0)
	c,conn = dbConnect()
	try:
		float(data[1])
		float(data[2])
	except ValueError:
		return 'Uso incorreto do comando.'
	if len(data) < 3:
		# Testar se o comando realmente está completo
		return 'Uso incorreto do comando.'
	else:
		data[1],data[2] = float(data[1]),float(data[2])
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
					c.execute('update users set reais = "%.2f" where nome = "%s"' % (novoSaldoComprador,nome))
					c.execute('update users set reais = "%.2f" where nome = "%s"' % (novoSaldoVendedor,vendedor))
					c.execute('delete from vendas where usuario = "%s" and preco = "%.2f" limit 1' % (vendedor,preco))
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
				c.execute('insert into compras(usuario,qntBTC,preco) values("%s",%.2f,%.2f)' % (nome,qntBTC,preco))
				c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoComprador,nome))
				conn.commit()
				return 'Ordem de compra realizada com sucesso.'
def vender(data):
	data.pop(0)
	c,conn = dbConnect()
	try:
		float(data[1])
		float(data[2])
	except ValueError:
		return 'Uso incorreto do comando.'
	if len(data) < 3:
		# Testar se o comando realmente está completo
		return 'Uso incorreto do comando.'
	else:
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
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoVendedor,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoComprador,comprador))
					c.execute('delete from compras where usuario = "%s" and preco = "%.2f" limit 1' % (comprador,preco))
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
					# Simplesmente realizar a compra.
					ex = c.execute('select reais from users where nome = "%s"' % nome)
					novoSaldoReais = ex.fetchone()
					novoSaldoReais = novoSaldoReais[0] + (qntBTC * preco)
					c.execute('update users set reais = %.2f where nome = "%s"' % (novoSaldoReais,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoVendedor,nome))
					c.execute('update users set btc = "%.8f" where nome = "%s"' % (novoSaldoComprador,comprador))
					c.execute('update compras set qntBTC = %.8f where usuario = "%s" and preco = "%.2f" limit 1' % (qntACompra - qntBTC,vendedor,preco))
					conn.commit()
					return 'Ordem de venda realizada com sucesso.'
			else:
				# Caso não haja um usuário comprando ao preço informado, 
				# abrir uma nova ordem de venda.
				novoSaldoVendedor = saldoVendedor - qntBTC
				c.execute('insert into vendas(usuario,qntBTC,preco) values("%s",%.2f,%.2f)' % (nome,qntBTC,preco))
				c.execute('update users set btc = %.8f where nome = "%s"' % (novoSaldoVendedor,nome))
				conn.commit()
				return 'Ordem de venda realizada com sucesso.'

def compras():
	c,conn = dbConnect()
	ex = c.execute('select * from compras')
	ex = ex.fetchall()
	data = ""
	for i in ex:
		for j in i:
			data += str(j)+","
		data += ";"
	if data == "":
		data = "semCompras"
	return data

def vendas():
	c,conn = dbConnect()
	ex = c.execute('select * from vendas')
	ex = ex.fetchall()
	data = ""
	for i in ex:
		for j in i:
			data += str(j)+","
		data += ";"
	if data == "":
		data = "semVendas"
	return data

def saldo(nome):
	c,conn = dbConnect()
	ex = c.execute('select reais from users where nome = "%s"' % nome)
	reais = ex.fetchone()[0]
	ex = c.execute('select btc from users where nome = "%s"' % nome)
	saldo = "%s,%s" % (str(reais),str(ex.fetchone()[0]))
	return saldo

def clientHandler(clientsocket,adress):
	print "Conexão de ",address
	data = clientsocket.recv(100)
	print 'Recebido: "%s"' % data
	data = data.split()
	retorno = ""
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
	clientsocket.sendall(retorno)
	
if __name__ == "__main__":
	# Configurando socket do servidor
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('', 7254))
	serversocket.listen(4)
	while True:
		clientsocket, address = serversocket.accept()
		thread.start_new_thread(clientHandler, (clientsocket, address))
