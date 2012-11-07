#!/bin/bash
##
## Instalacao Ambiente de Desenvolvimento
##

# nome do ambiente
environment=$1

if [ $(whoami) != "root" ]; then
  echo "Tem que executar como root."
  exit 2
fi

##
## Configuracoes Basicas de Desenvolvimento
##
ConfigureDevel()
{
    # desativa selinux
    [ -f /etc/selinux/config ] && sed -i.backup -e 's/^SELINUX=.*$/SELINUX=disabled/' /etc/selinux/config

    # configura editor svn
    if ! grep -q "SVN_EDITOR" /etc/bashrc ; then
        if [ -x /usr/bin/vim ] ; then 
            printf 'export SVN_EDITOR=/usr/bin/vim\n'>> /etc/bashrc
        else
            printf 'export SVN_EDITOR=/usr/bin/vi\n'>> /etc/bashrc
        fi
    fi

    # Melhorando visual bash
    cat << SETVAR >> /etc/bashrc
if [ "$(id -u)" != "0" ] ; then
    PS1="\n(\e[31;1m\u\e[m - \w @\e[32;1m\t\e[m - Devel :: $environment) \n\H: "
else
    PS1="\n(\e[34;1m\u\e[m - \w @\e[32;1m\t\e[m - Devel :: $environment) \n\H: "
fi
SETVAR
}

##
## Instala os pacotes necessarios para um ambiente de desenvolvimento
##
InstallPackages() {

    printf "\n           Instalando Pacotes  "
    printf "\n------------------------------------------------------------\n"

    # instando EPEL
    wget "http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm" -qO "/tmp/epel.rpm"
    rpm -ivh /tmp/epel.rpm

    # instalando Pacotes necessarios para desenvolvimento
    yumList=("php-pear curl gettext make man man-pages python-crypto python-hashlib
        python-nose python-simplejson python-twisted python-uuid rpm-build"
        "selinux-policy selinux-policy-targeted subversion sudo syslinux"
        "vim-enhanced wget yum-changelog yum-security yum-utils screen"
        "automake make rpm rpm-build rpm-devel curl-devel openssl-devel mysql"
        "mysql-server httpd gettext php php-devel php-mbstring php-mysql autoconf "
        "php-pdo php-xml php-gd php-pear php-pear-PHP-CodeSniffer php-pear-PHPUnit"
        "mod_ssl python python-twisted python-simplejson python-pycurl python-hashlib");
    yum install $(printf "%s" "${yumList[@]}") -y

    # Pacotes de Ferramentas de Desenvolvedor
    yum groupinstall -y 'Development Tools'
}

##
## Node nao e querido, asm valido ter
##
InstallNode() {

    printf " INSTALADO Node JS, aguarde isto vai demorar ... \n\n";

    wget "http://nodejs.org/dist/v0.8.1/node-v0.8.1.tar.gz" -O "node-v0.8.1.tar.gz"
    tar -vzxf node-v0.8.1.tar.gz
    cd node-v0.8.1; ./configure; make; make install
    rm -rf node-v0.8.1; rm-rf node-v0.8.1.tar.gz
}

##
## Instalando Softwares para Integracao continua em PHP
##
InstallICPHP() {

    # instalando Code Sniffer
    pear channel-update pear.php.net
    pear install PHP_CodeSniffer-1.4.1

    # instalando PHP Documentor
    pear channel-discover pear.phpdoc.org
    pear install phpdoc/phpDocumentor-alpha

    # PHP Unit
    pear channel-discover pear.phpunit.de
    pear channel-discover components.ez.no
    pear channel-discover pear.symfony-project.com
    pear channel-update pear.phpunit.de
    pear install pear.phpunit.de/PHPUnit
    pear install pear.phpunit.de/phpcpd
    pear install pear.phpunit.de/phploc
    pear install pear.phpunit.de/PHP_CodeCoverage

    # php depend
    pear channel-discover pear.pdepend.org
    pear channel-update pear.pdepend.org
    pear install pdepend/PHP_Depend-beta
}

# executando lista de acoes

# executa Instalacao de Pacotes
InstallPackages;

# Configurando ambiente de Desenvolvimento
ConfigureDevel;

# integracao continua
InstallICPHP;

InstallNode;