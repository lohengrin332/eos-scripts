#!/bin/bash

run='/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper'

$run begin
$run delete service dns forwarding options 'log-queries'
$run commit
$run save
