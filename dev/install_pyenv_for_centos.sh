#pyenv deps
sudo yum -y install zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel git
sudo yum -y install python-pip
sudo yum -y groupinstall "Development Tools"

./install_and_configure_pyenv.sh
