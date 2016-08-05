<?php
require_once("easybitcoin.php");
$bitcoin = new Bitcoin("admin","root");
$txid = $_GET["tx"];
$txinfo = $bitcoin->gettransaction($txid);
$qntBTC = $txinfo["amount"];
$account = $txinfo["details"][0]["account"];
$confirm = $txinfo["confirmations"];
if (($confirm == 0) && ($qntBTC > 0)){
	$fp = fsockopen("127.0.0.1", 7254, $errno, $errstr, 30);

	fwrite($fp, "deposito ".$qntBTC." ".$account);
	fclose($fp);
}

?>
