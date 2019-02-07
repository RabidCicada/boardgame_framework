#Install pyenv and configure 3.6/3.7
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer -o pyenv-installer.sh
chmod 777 pyenv-installer.sh
./pyenv-installer.sh
touch ~/.bash_profile
cat >> ~/.bash_profile <<'ZZZBBB'
#Specifically a fix for Ubuntu on Windows
if [ -f ~/.bashrc ] ; then
        . ~/.bashrc
fi

export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
ZZZBBB
source ~/.bash_profile
pyenv install 3.7.0
pyenv virtualenv 3.7.0 bgfw_dev
