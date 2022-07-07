#!/bin/bash

run='/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper'

$run begin
$run delete firewall modify balance rule 70 modify lb-group G
$run set firewall modify balance rule 70 modify lb-group B
$run commit
$run save
