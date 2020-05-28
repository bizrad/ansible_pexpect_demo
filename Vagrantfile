# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # NOTE edit this as needed. This should match your computer and network. These settings are for a mac.
  config.vm.network "public_network", bridge: "en0: Wi-Fi (AirPort)", auto_config: false
  config.vm.provision "shell", run: "always", inline: "ip addr add 192.168.0.115 dev eth1"

  # NOTE be sure you have a local ssh key in ~/.ssh/ edit the name as needed
  config.ssh.insert_key = false
  config.ssh.private_key_path = ['~/.vagrant.d/insecure_private_key', '~/.ssh/id_rsa']
  config.vm.provision "file", source: "~/.ssh/id_rsa.pub", destination: "~/.ssh/authorized_keys"
  config.vm.provision "shell", inline: <<-EOC
    sudo sed -i -e "\\#PasswordAuthentication yes# s#PasswordAuthentication yes#PasswordAuthentication no#g" /etc/ssh/sshd_config
    sudo systemctl restart sshd.service
    echo "finished"
  EOC

  config.vm.box = "centos/8"
end
