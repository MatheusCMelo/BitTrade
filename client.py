#coding: utf-8
# Matheus da Cunha Melo Almeida
# 115210030
# matheus.almeida@ccc.ufcg.edu.br
# BitTrade
# Client
import socket
import os
import time
import sys
from operator import itemgetter
import getpass

def sendData(msg): # Função de envio e recebimento de dados
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(("45.55.192.160", 7254))
	s.sendall(msg)
	data = s.recv(1000)
	return data

def main(nome): # Função principal
	time.sleep(2)
	clear()
	print "Bem vindo, %s, à tela inicial da BitTrade." % nome
	print "Aqui você pode digitar os comandos que quiser executar."
	print "Digite 'ajuda' para obter a lista completa de comandos."
	while True:
		# Lida com vários casos de comandos
		msg = raw_input('> ')
		msg2 = msg.split()
		if msg == "":None
		elif msg2[0] == 'ajuda':
			print "'comprar Q P' = Cria uma ordem de compra. Substitua Q pela quantidade de Bitcoins e P pelo preço em reais."
			print "'vender Q P' = Cria uma ordem de venda. Substitua Q pela quantidade de Bitcoins e P pelo preço em reais."
			print "'cancelar (compra/venda) Q P' = Cancelar uma ordem de compra/venda. Substitua Q pela quantidade a venda e P pelo preço."
			print "'vendas' = Mostra a lista de ordens de venda."
			print "'compras' = Mostra a lista de ordens de compra."
			print "'saldo' = Mostra seu saldo em reais e em Bitcoins."
			print "'depositar' = Mostra seu endereço para depósito de Bitcoins."
			print "'sacar' = Lhe permite sacar seu saldo em Bitcoins."
			print "Digite 'limpar' para limpar a tela."
			print "Digite 'sair' para deslogar e fechar o programa."
		elif msg2[0] == 'sair':
			sys.exit(0)
		elif msg2[0] == 'limpar':
			clear()
		elif msg2[0] == 'compras':
			retorno = sendData(msg)
			if retorno == None:None
			elif retorno != "semCompras":
				retorno = retorno.split(';')
				retorno.pop(-1)
				for i in range(len(retorno)):
					retorno[i] = retorno[i].split(',')
				for i in range(len(retorno)):
					retorno[i][1] = float(retorno[i][1])
					retorno[i][2] = float(retorno[i][2])
				retorno = sorted(retorno, key=itemgetter(2))
				for i in range(len(retorno)):
					print "%.8f BTC a R$ %.2f"%(retorno[i][1],retorno[i][2])
			else:
				print "Não há ordens de compra no momento."
		elif msg2[0] == 'vendas':
			retorno = sendData(msg)
			if retorno != "semVendas":
				retorno = retorno.split(';')
				retorno.pop(-1)
				for i in range(len(retorno)):
					retorno[i] = retorno[i].split(',')
				for i in range(len(retorno)):
					retorno[i][1] = float(retorno[i][1])
					retorno[i][2] = float(retorno[i][2])
				retorno = sorted(retorno, key=itemgetter(2))
				for i in range(len(retorno)):
					print "%.8f BTC a R$ %.2f"%(retorno[i][1],retorno[i][2])
			else:
				print "Não há ordens de venda no momento."
		elif msg2[0] == 'comprar':
			if len(msg2) == 3:
				msg = '%s %s %s %s' % ('comprar',nome,msg2[1],msg2[2])
				print sendData(msg)
			else:
				print 'Uso incorreto do comando.'
		elif msg2[0] == 'vender':
			if len(msg2) == 3:
				msg = '%s %s %s %s' % ('vender',nome,msg2[1],msg2[2])
				print sendData(msg)
			else:
				print 'Uso incorreto do comando.'
		elif msg2[0] == 'saldo':
			msg = '%s %s' % ('saldo',nome)
			retorno = sendData(msg).split(",")
			print "Seu saldo é de R$ %.2f e %.8f BTC" % (float(retorno[0]),float(retorno[1]))
		elif msg2[0] == 'depositar':			
			msg = 'depositar %s' % nome
			address = sendData(msg)
			print 'Seu endereço para depósito é: %s' % address
		elif msg2[0] == 'cancelar':
			if len(msg2) != 4:
				print "Uso incorreto do comando."
			else:
				msg = 'cancelar %s %s %s %s' % (msg2[1],msg2[2],msg2[3],nome)
				print sendData(msg)
		elif msg2[0] == 'sacar':
			print "Aqui você pode sacar seus Bitcoins. Observe que a taxa de transferência é de 0.0002 BTC."
			qntBTC = raw_input('Quantidade de Bitcoins: ')
			address = raw_input('Endereço da carteira para depósito: ')
			print sendData('saque %s %s %s' % (qntBTC,address,nome))
		elif msg2[0] in comandos:
			print sendData(msg)
		else:
			print "Comando não identificado. Digite 'ajuda' para obter uma lista de comandos disponíveis."
def login(): # Função de login
	clear()
	while True:
		nome = raw_input("Nome de usuário: ")
		senha = getpass.getpass("Senha: ")
		response = sendData('login %s %s' % (nome,senha))
		if response == "naocadastrado": # Se não cadastrado
			clear()
			entrada = raw_input('Este usuário não existe. Deseja cadastrar-se? (s/n)')
			if entrada == 's':
				cadastro()
				break
			elif entrada == 'n':
				clear()
		elif response == 'usuariosenha': # Se usuário ou senha incorretos
			print "Usuário ou senha incorretos."
			time.sleep(1)
			clear()
		elif response == 'sucesso':
			print "Logado com sucesso!"
			main(nome)

def cadastro(): # Função de cadastro
	clear()
	print "Bem vindo ao cadastro."
	print "Aqui você pode cadastrar uma nova conta para utilizar o BitTrade."
	print "Digite um nome de usuário e em seguida uma senha abaixo."
	while True:
		nome = raw_input("Nome de usuário: ")
		senha = getpass.getpass("Senha: ")
		response = sendData('cadastro %s %s' % (nome,senha))
		if response == "jc": # Se já cadastrado
			clear()
			print "Parece que já temos um usuário com este nome. Por favor, escolha outro."
		elif response == "sucesso":
			clear()
			print "Usuário cadastrado com sucesso!"
			main(nome)

clear = lambda: os.system('clear') # Função para limpar a tela

comandos = ['vender','saldo','comprar','vendas','compras','sair','depositar','cancelar','sacar'] # Comandos permitidos

if __name__ == "__main__": # Tela inicial
	clear()
	while True:
		print "Bem vindo à BitTrade!"
		print "Digite 'login' se você já é cadastrado ou 'cadastro' se quiser criar uma nova conta!"
		entrada = raw_input('> ')
		if entrada == 'cadastro':
			cadastro()
			break
		elif entrada == 'login':
			login()
		else:
			clear()
