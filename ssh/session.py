# -*- coding: utf-8 -*-
# Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from dataclasses import dataclass
from typing import List, NoReturn, Optional, Tuple, Union

import paramiko

@dataclass
class Command():
    cmd: str
    input: Optional[str] = None

@dataclass
class Result():
    data: str
    status: int
    error: str = ""

class Session():
    
    def __init__(self,
        hostaddr: str,
        username: str,
        password: str = "",
        keyfile: Optional[str] = None,
        passphrase: Optional[str] = None,
        timeout: Union[int, Tuple[int, int], Tuple[int, int, int]] = 30,
        port: int = 22):

        self.hostaddr = hostaddr
        self.port = port
        self.username = username
        self.password = password
        self.keyfile = keyfile
        self.passphrase = passphrase
        self.timeout = timeout
        self._client = paramiko.SSHClient()

    @property
    def _connection(self) -> paramiko.SSHClient:

        if self.is_alive():
            return self._client

        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(
            self.hostaddr,
            username=self.username,
            password=self.password,
            key_filename=self.keyfile,
            passphrase=self.passphrase,
            timeout=self.timeout
        )
        
        return self._client
    
    def is_alive(self):
        try:
            transport = self._client.get_transport()
            if transport is not None:
                transport.send_ignore()
                return True
        except EOFError as exc:
            pass
        
        return False

    def close(self) -> NoReturn:
        if self.is_alive():
            self._client.close()

    def send(self, commands: List[Union[str, Command]]) -> list:
        results = []
        for _cmd in commands:
            cmd = _cmd
            input = None

            if isinstance(_cmd, Command):
                cmd = _cmd.cmd
                input = _cmd.input

            stdin, stdout, stderr = self._connection.exec_command(cmd)

            if input is not None:
                stdin.channel.send(input + "\n")
                stdin.channel.shutdown_write()
            
            status = stdout.channel.recv_exit_status()
            
            results.append(Result(stdout.read(), status, stderr.read()))
        
        return results
