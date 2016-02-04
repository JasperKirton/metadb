# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

NCPUS = ENV['MDB_NCPUS'] || '1'
MEM = ENV['MDB_MEM'] || '1024'
MIRROR = ENV['MDB_MIRROR'] || 'archive.ubuntu.com'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.hostname = "metadb"

  config.vm.provider "virtualbox" do |v|
    v.memory = MEM.to_i
    v.cpus = NCPUS.to_i
  end

  # Use a custom vm name
  config.vm.define :metadb do |t|
  end

  config.vm.provision :shell, path: "admin/bootstrap.sh"
  config.vm.provision :shell, path: "admin/setup_app.sh", args: "/home/vagrant/metadb", privileged: false

  config.vm.synced_folder ".", "/home/vagrant/metadb"

  # Web server forwarding:
  config.vm.network "forwarded_port", guest: 8080, host: 8080

  # PostgreSQL forwarding:
  config.vm.network "forwarded_port", guest: 5432, host: 15432

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network "private_network", ip: "192.168.33.10"
end
